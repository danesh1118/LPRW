"""Shared relay helpers — optimized for low latency on Railway."""
from __future__ import annotations

import asyncio
import logging
import socket
import time

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("LPRW.relay")

# Larger buffers + aggressive TCP tuning for throughput
RELAY_BUF = 512 * 1024
SOCK_BUF = 2 * 1024 * 1024
WRITE_HIGH_WATER = 256 * 1024

QUOTA_MIN_BATCH = 64 * 1024
QUOTA_MAX_BATCH = 4 * 1024 * 1024
QUOTA_START_BATCH = 256 * 1024
QUOTA_CHECK_INTERVAL = 0.5


def tune_socket(writer: asyncio.StreamWriter):
    try:
        sock = writer.transport.get_extra_info("socket")
        if not sock:
            return
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCK_BUF)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUF)
        if hasattr(socket, "SO_KEEPALIVE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, "TCP_QUICKACK"):
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
            except OSError:
                pass
        if hasattr(socket, "TCP_KEEPIDLE"):
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            except OSError:
                pass
    except OSError:
        pass


class QuotaGate:
    __slots__ = ("uuid", "pending", "last_check", "ok", "batch_bytes", "rate_ewma", "on_usage")

    def __init__(self, uuid: str, on_usage):
        self.uuid = uuid
        self.on_usage = on_usage
        self.pending = 0
        self.last_check = time.monotonic()
        self.ok = True
        self.batch_bytes = QUOTA_START_BATCH
        self.rate_ewma = 0.0

    def _call(self, n: int) -> bool:
        return bool(self.on_usage(self.uuid, n))

    async def add(self, nbytes: int) -> bool:
        if not self.ok:
            return False
        self.pending += nbytes
        now = time.monotonic()
        elapsed = now - self.last_check
        if self.pending >= self.batch_bytes or elapsed >= QUOTA_CHECK_INTERVAL:
            flush, self.pending = self.pending, 0
            if elapsed > 0:
                inst = flush / elapsed
                self.rate_ewma = inst if not self.rate_ewma else (0.7 * self.rate_ewma + 0.3 * inst)
                target = int(self.rate_ewma * QUOTA_CHECK_INTERVAL)
                self.batch_bytes = max(QUOTA_MIN_BATCH, min(QUOTA_MAX_BATCH, target or QUOTA_MIN_BATCH))
            self.last_check = now
            try:
                self.ok = self._call(flush)
            except Exception:
                self.ok = False
            return self.ok
        return True

    async def flush(self) -> bool:
        if self.pending:
            flush, self.pending = self.pending, 0
            try:
                self.ok = self.ok and self._call(flush)
            except Exception:
                self.ok = False
        return self.ok


async def open_tcp(address: str, port: int, timeout: float = 8.0):
    """IPv4-first connect to avoid slow IPv6 paths."""
    loop = asyncio.get_running_loop()
    last_err = None
    try:
        infos = await loop.getaddrinfo(
            address, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
    except Exception as e:
        raise OSError(f"dns failed {address}: {e}") from e

    infos = sorted(infos, key=lambda x: 0 if x[0] == socket.AF_INET else 1)
    for family, type_, proto, _, sockaddr in infos:
        sock = None
        try:
            sock = socket.socket(family, type_, proto)
            sock.setblocking(False)
            await asyncio.wait_for(loop.sock_connect(sock, sockaddr), timeout=timeout)
            reader, writer = await asyncio.open_connection(sock=sock)
            return reader, writer
        except Exception as e:
            last_err = e
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
    return await asyncio.wait_for(asyncio.open_connection(address, port), timeout=timeout)


async def relay_ws_to_tcp(ws: WebSocket, writer: asyncio.StreamWriter, gate: QuotaGate):
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            data = msg.get("bytes") or (msg.get("text") or "").encode()
            if not data:
                continue
            if not await gate.add(len(data)):
                try:
                    await ws.close(code=1008)
                except Exception:
                    pass
                break
            writer.write(data)
            if writer.transport.get_write_buffer_size() > WRITE_HIGH_WATER:
                await writer.drain()
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        await gate.flush()
        try:
            writer.write_eof()
        except Exception:
            pass


async def relay_tcp_to_ws(ws: WebSocket, reader: asyncio.StreamReader, gate: QuotaGate, prefix: bytes = b""):
    first = True
    try:
        while True:
            data = await reader.read(RELAY_BUF)
            if not data:
                break
            if not await gate.add(len(data)):
                try:
                    await ws.close(code=1008)
                except Exception:
                    pass
                break
            if first and prefix:
                await ws.send_bytes(prefix + data)
                first = False
            else:
                await ws.send_bytes(data)
    except Exception:
        pass
    finally:
        await gate.flush()


async def bidirectional_relay(ws, reader, writer, gate, vless_ack: bool = False):
    """Run both directions; cancel sibling when one finishes."""
    if vless_ack:
        try:
            await ws.send_bytes(b"\x00\x00")
        except Exception:
            return
    t1 = asyncio.create_task(relay_ws_to_tcp(ws, writer, gate))
    t2 = asyncio.create_task(relay_tcp_to_ws(ws, reader, gate, prefix=b""))
    done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass

"""LPRW Trojan relay — WebSocket."""
from __future__ import annotations

import asyncio
import logging
import socket

from fastapi import WebSocket, WebSocketDisconnect

from protocol.common import QuotaGate, bidirectional_relay, open_tcp, tune_socket

logger = logging.getLogger("LPRW.trojan")


def parse_trojan_header(data: bytes):
    if b"\r\n" not in data:
        raise ValueError("no crlf")
    pw_b, rest = data.split(b"\r\n", 1)
    password = pw_b.decode("utf-8", "ignore").strip()
    if rest.startswith(b"\r\n"):
        rest = rest[2:]
    if len(rest) < 7:
        raise ValueError("short request")
    cmd = rest[0]
    atyp = rest[1]
    pos = 2
    if atyp == 0x01:
        address = socket.inet_ntop(socket.AF_INET, rest[pos : pos + 4])
        pos += 4
    elif atyp == 0x03:
        n = rest[pos]
        pos += 1
        address = rest[pos : pos + n].decode("utf-8", "ignore")
        pos += n
    elif atyp == 0x04:
        address = socket.inet_ntop(socket.AF_INET6, rest[pos : pos + 16])
        pos += 16
    else:
        raise ValueError(f"bad atyp {atyp}")
    port = int.from_bytes(rest[pos : pos + 2], "big")
    pos += 2
    return password, cmd, address, port, rest[pos:]


async def handle_trojan_ws(ws, password, is_allowed, on_usage, register_conn, unregister_conn):
    await ws.accept()
    link = is_allowed(password)
    if not link:
        await ws.close(code=1008, reason="not authorized")
        return

    conn_id = register_conn(password)
    writer = None
    try:
        first_msg = await asyncio.wait_for(ws.receive(), timeout=12.0)
        if first_msg["type"] == "websocket.disconnect":
            return
        first_chunk = first_msg.get("bytes") or (first_msg.get("text") or "").encode()
        if not first_chunk:
            return

        _, cmd, address, port, payload = parse_trojan_header(first_chunk)
        gate = QuotaGate(password, on_usage)
        if not await gate.add(len(first_chunk)):
            await ws.close(code=1008, reason="quota")
            return
        if cmd != 0x01:
            await ws.close(code=1008, reason="udp not supported")
            return

        reader, writer = await open_tcp(address, port, timeout=8.0)
        tune_socket(writer)

        if payload:
            writer.write(payload)
            await writer.drain()
            await gate.add(len(payload))

        await bidirectional_relay(ws, reader, writer, gate, vless_ack=False)
    except (WebSocketDisconnect, Exception) as e:
        logger.debug("trojan: %s", e)
    finally:
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        unregister_conn(conn_id)



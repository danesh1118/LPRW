"""LPRW VLESS relay — WebSocket."""
from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from protocol.common import (
    QuotaGate,
    bidirectional_relay,
    open_tcp,
    tune_socket,
)

logger = logging.getLogger("LPRW.vless")


def parse_vless_header(chunk: bytes):
    if len(chunk) < 24:
        raise ValueError("chunk too small")
    pos = 1
    pos += 16
    addon_len = chunk[pos]
    pos += 1 + addon_len
    command = chunk[pos]
    pos += 1
    port = int.from_bytes(chunk[pos : pos + 2], "big")
    pos += 2
    addr_type = chunk[pos]
    pos += 1
    if addr_type == 1:
        address = ".".join(str(b) for b in chunk[pos : pos + 4])
        pos += 4
    elif addr_type == 2:
        dlen = chunk[pos]
        pos += 1
        address = chunk[pos : pos + dlen].decode("utf-8", errors="ignore")
        pos += dlen
    elif addr_type == 3:
        ab = chunk[pos : pos + 16]
        pos += 16
        address = ":".join(f"{ab[i]:02x}{ab[i+1]:02x}" for i in range(0, 16, 2))
    else:
        raise ValueError(f"unknown addr type: {addr_type}")
    return command, address, port, chunk[pos:]


async def handle_vless_ws(ws, uuid, is_allowed, on_usage, register_conn, unregister_conn):
    await ws.accept()
    link = is_allowed(uuid)
    if not link:
        await ws.close(code=1008, reason="not authorized")
        return

    conn_id = register_conn(uuid)
    writer = None
    try:
        first_msg = await asyncio.wait_for(ws.receive(), timeout=12.0)
        if first_msg["type"] == "websocket.disconnect":
            return
        first_chunk = first_msg.get("bytes") or (first_msg.get("text") or "").encode()
        if not first_chunk:
            return

        command, address, port, payload = parse_vless_header(first_chunk)
        gate = QuotaGate(uuid, on_usage)
        if not await gate.add(len(first_chunk)):
            await ws.close(code=1008, reason="quota")
            return
        if command != 0x01:
            await ws.close(code=1008, reason="udp not supported")
            return

        reader, writer = await open_tcp(address, port, timeout=8.0)
        tune_socket(writer)

        # Immediate VLESS response — reduces client stall
        await ws.send_bytes(b"\x00\x00")

        if payload:
            writer.write(payload)
            await writer.drain()
            await gate.add(len(payload))

        await bidirectional_relay(ws, reader, writer, gate, vless_ack=False)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        logger.debug("vless error: %s", e)
    finally:
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        unregister_conn(conn_id)

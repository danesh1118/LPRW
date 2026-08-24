"""LPRW Shadowsocks AEAD (aes-256-gcm / chacha20-ietf-poly1305) over WebSocket."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import socket
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from fastapi import WebSocket, WebSocketDisconnect

from protocol.common import RELAY_BUF, WRITE_HIGH_WATER, QuotaGate, open_tcp, tune_socket

logger = logging.getLogger("LPRW.ss")

TAG_LEN = 16
NONCE_LEN = 12
# AEAD length chunk: 2-byte len + tag, then payload + tag
SALSA_SUBKEY = b"ss-subkey"


def _evp_bytes_to_key(password: bytes, key_len: int) -> bytes:
    m = []
    i = 0
    while len(b"".join(m)) < key_len:
        data = password if i == 0 else m[i - 1] + password
        m.append(hashlib.md5(data).digest())
        i += 1
    return b"".join(m)[:key_len]


def derive_key(password: str, method: str) -> bytes:
    key_len = 32
    return _evp_bytes_to_key(password.encode("utf-8"), key_len)


def make_aead(method: str, key: bytes, nonce: bytes):
    if method in ("aes-256-gcm", "aes-128-gcm"):
        return AESGCM(key)
    if method in ("chacha20-ietf-poly1305", "xchacha20-ietf-poly1305"):
        return ChaCha20Poly1305(key)
    raise ValueError(f"unsupported method {method}")


class AEADCipher:
    """Shadowsocks 2022-style AEAD stream (classic AEAD per chunk)."""

    def __init__(self, method: str, key: bytes, encrypt: bool):
        self.method = method
        self.key = key
        self.encrypt = encrypt
        self.nonce_counter = 0
        self.salt = os.urandom(32)
        # subkey via HKDF-like: blake2 or simple hash for classic SS AEAD
        sub = hashlib.sha1(self.salt + key).digest()
        if len(sub) < 32:
            sub = hashlib.sha256(self.salt + key).digest()
        self.session_key = sub[:32]
        self._buf = b""

    def _nonce(self) -> bytes:
        n = self.nonce_counter.to_bytes(NONCE_LEN, "little")
        self.nonce_counter += 1
        return n

    def seal(self, data: bytes) -> bytes:
        aead = make_aead(self.method, self.session_key, b"\x00" * NONCE_LEN)
        out = b""
        # length
        ln = len(data)
        len_bytes = struct.pack("!H", ln)
        n1 = self._nonce()
        out += aead.encrypt(n1, len_bytes, None)
        n2 = self._nonce()
        out += aead.encrypt(n2, data, None)
        return out

    def open_chunk(self, data: bytes) -> tuple[bytes, bytes]:
        """Decrypt one chunk from buffer; returns (plaintext, remaining)."""
        aead = make_aead(self.method, self.session_key, b"\x00" * NONCE_LEN)
        self._buf += data
        # need 2+TAG for length
        if len(self._buf) < 2 + TAG_LEN:
            return b"", self._buf
        n1 = self._nonce()
        try:
            len_plain = aead.decrypt(n1, self._buf[: 2 + TAG_LEN], None)
        except Exception:
            # reset nonce counter on failure path — caller should drop
            raise
        ln = struct.unpack("!H", len_plain)[0]
        need = 2 + TAG_LEN + ln + TAG_LEN
        if len(self._buf) < need:
            # rewind nonce
            self.nonce_counter -= 1
            return b"", self._buf
        chunk = self._buf[2 + TAG_LEN : need]
        rest = self._buf[need:]
        self._buf = b""
        n2 = self._nonce()
        plain = aead.decrypt(n2, chunk, None)
        return plain, rest


def parse_ss_addr(data: bytes):
    if not data:
        raise ValueError("empty")
    atyp = data[0]
    pos = 1
    if atyp == 0x01:
        address = socket.inet_ntop(socket.AF_INET, data[pos : pos + 4])
        pos += 4
    elif atyp == 0x03:
        n = data[pos]
        pos += 1
        address = data[pos : pos + n].decode("utf-8", "ignore")
        pos += n
    elif atyp == 0x04:
        address = socket.inet_ntop(socket.AF_INET6, data[pos : pos + 16])
        pos += 16
    else:
        raise ValueError(f"bad atyp {atyp}")
    port = int.from_bytes(data[pos : pos + 2], "big")
    pos += 2
    return address, port, data[pos:]


async def handle_ss_ws(ws, link_id, is_allowed, on_usage, register_conn, unregister_conn, method="aes-256-gcm"):
    """
    Shadowsocks over WebSocket:
    Client sends: salt(32) + AEAD(target header + payload)...
    Compatible with clients that tunnel SS through WS (custom path).
    """
    await ws.accept()
    link = is_allowed(link_id)
    if not link:
        await ws.close(code=1008, reason="not authorized")
        return

    password = link.get("ss_password") or link_id
    method = link.get("ss_method") or method
    key = derive_key(password, method)

    conn_id = register_conn(link_id)
    writer = None
    try:
        first_msg = await asyncio.wait_for(ws.receive(), timeout=12.0)
        if first_msg["type"] == "websocket.disconnect":
            return
        raw = first_msg.get("bytes") or b""
        if len(raw) < 32:
            await ws.close(code=1008, reason="short")
            return

        salt = raw[:32]
        rest = raw[32:]
        # session key from salt + master key
        session_key = hashlib.sha256(salt + key).digest()
        dec = _SSStream(method, session_key, encrypt=False)
        enc = _SSStream(method, session_key, encrypt=True)
        # prepend salt to first response path not needed for server

        gate = QuotaGate(link_id, on_usage)
        await gate.add(len(raw))

        plain, leftover = dec.feed(rest)
        if not plain:
            # need more data
            while not plain:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    return
                chunk = msg.get("bytes") or b""
                await gate.add(len(chunk))
                plain, leftover = dec.feed(chunk)

        address, port, payload = parse_ss_addr(plain)
        reader, writer = await open_tcp(address, port, timeout=8.0)
        tune_socket(writer)

        if payload:
            writer.write(payload)
            await writer.drain()
            await gate.add(len(payload))
        if leftover:
            # more decrypted already in buffer handled by feed
            pass

        async def ws_to_tcp():
            try:
                buf_plain = leftover
                if buf_plain:
                    writer.write(buf_plain)
                    await writer.drain()
                while True:
                    msg = await ws.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    data = msg.get("bytes") or b""
                    if not data:
                        continue
                    if not await gate.add(len(data)):
                        break
                    p, _ = dec.feed(data)
                    if p:
                        writer.write(p)
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

        async def tcp_to_ws():
            try:
                # first response includes salt for client
                first = True
                while True:
                    data = await reader.read(RELAY_BUF)
                    if not data:
                        break
                    if not await gate.add(len(data)):
                        break
                    sealed = enc.seal(data)
                    if first:
                        await ws.send_bytes(salt + sealed)
                        first = False
                    else:
                        await ws.send_bytes(sealed)
            except Exception:
                pass
            finally:
                await gate.flush()

        t1 = asyncio.create_task(ws_to_tcp())
        t2 = asyncio.create_task(tcp_to_ws())
        done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        logger.debug("ss error: %s", e)
    finally:
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        unregister_conn(conn_id)


class _SSStream:
    def __init__(self, method: str, session_key: bytes, encrypt: bool):
        self.method = method
        self.key = session_key
        self.encrypt = encrypt
        self.nonce_c = 0
        self._buf = b""

    def _nonce(self):
        n = self.nonce_c.to_bytes(12, "little")
        self.nonce_c += 1
        return n

    def _aead(self):
        if self.method.startswith("aes"):
            return AESGCM(self.key)
        return ChaCha20Poly1305(self.key)

    def seal(self, data: bytes) -> bytes:
        aead = self._aead()
        out = aead.encrypt(self._nonce(), struct.pack("!H", len(data)), None)
        out += aead.encrypt(self._nonce(), data, None)
        return out

    def feed(self, data: bytes) -> tuple[bytes, bytes]:
        """Return (decrypted_payload_so_far, unconsumed). Accumulates full chunks."""
        aead = self._aead()
        self._buf += data
        out = b""
        while True:
            if len(self._buf) < 2 + TAG_LEN:
                break
            # peek length without consuming nonce permanently on failure
            saved = self.nonce_c
            try:
                n1 = self.nonce_c.to_bytes(12, "little")
                len_p = aead.decrypt(n1, self._buf[: 2 + TAG_LEN], None)
            except Exception:
                self.nonce_c = saved
                break
            self.nonce_c = saved + 1
            ln = struct.unpack("!H", len_p)[0]
            need = 2 + TAG_LEN + ln + TAG_LEN
            if len(self._buf) < need:
                self.nonce_c = saved
                break
            body = self._buf[2 + TAG_LEN : need]
            self._buf = self._buf[need:]
            n2 = self.nonce_c.to_bytes(12, "little")
            self.nonce_c += 1
            try:
                out += aead.decrypt(n2, body, None)
            except Exception:
                break
        return out, self._buf

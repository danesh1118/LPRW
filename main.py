"""
LPRW — Leviko Panel Railway v4.0
Multi-protocol gateway: VLESS / Trojan / Shadowsocks
Transport: WebSocket only
Inbound-based config management.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import shutil
import secrets
import time
import uuid as uuidlib
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import aiofiles
import qrcode
from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from protocol.vless import handle_vless_ws
from protocol.trojan import handle_trojan_ws
from protocol.shadowsocks import handle_ss_ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("LPRW")

VERSION = "4.12.0"
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATA_FILE = DATA_DIR / "lprw.json"
SECRET_FILE = DATA_DIR / ".secret"
TZ = timezone(timedelta(hours=3, minutes=30))
COOKIE = "lprw_sid"
TTL = 86400 * 7

# ── helpers ──────────────────────────────────────────────────────────────────

def _secret() -> str:
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if SECRET_FILE.exists():
            v = SECRET_FILE.read_text().strip()
            if v:
                return v
        n = secrets.token_urlsafe(40)
        SECRET_FILE.write_text(n)
        return n
    except Exception:
        return secrets.token_urlsafe(40)


SECRET = _secret()
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "12345")
PORT = int(os.environ.get("PORT", 8000))


def host(request: Optional[Request] = None) -> str:
    candidates = []
    for key in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_STATIC_URL", "PUBLIC_HOST", "HOST", "DOMAIN"):
        v = (os.environ.get(key) or "").strip()
        if v:
            candidates.append(v)
    ph = (SETTINGS.get("public_host") or "").strip()
    if ph:
        candidates.append(ph)
    if request is not None:
        for hk in ("x-forwarded-host", "x-original-host", "host"):
            raw = (request.headers.get(hk) or "").split(",")[0].strip()
            if raw:
                candidates.append(raw)
        try:
            if request.url.hostname:
                candidates.append(request.url.hostname)
        except Exception:
            pass
    cleaned = []
    for h in candidates:
        h = (h or "").replace("https://", "").replace("http://", "").split("/")[0].strip()
        if not h:
            continue
        if ":" in h and not h.startswith("["):
            host_part, _, port = h.rpartition(":")
            if port.isdigit() and port in ("80", "443"):
                h = host_part
        if h and h not in cleaned:
            cleaned.append(h)
    for h in cleaned:
        if h not in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            return h
    return cleaned[0] if cleaned else "localhost"


def now() -> datetime:
    return datetime.now(TZ)


def hp(p: str) -> str:
    return hashlib.sha256(f"{p}{SECRET}".encode()).hexdigest()


def bh(n: float) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} PB"


_admin = hp(ADMIN_PW)
LINKS: dict = {}
SUBS: dict = {}
INBOUNDS: dict = {}
SESS: dict = {}
CONNECTIONS: dict = {}
STATS = {"bytes": 0, "reqs": 0, "errors": 0, "start": time.time()}
ACT: deque = deque(maxlen=500)
HOURLY: dict = defaultdict(int)
SETTINGS = {
    "panel_name": os.environ.get("PANEL_NAME", "LPRW"),
    "admin_user": ADMIN_USER,
    "announce": "",
    "support_url": "",
    "outbound_enabled": False,
    "outbound_remove_primary": False,
    "outbound_remove_status": False,
    "outbound_configs": [],
}
LLOCK = asyncio.Lock()
SLOCK = asyncio.Lock()
ILOCK = asyncio.Lock()
XLOCK = asyncio.Lock()
SAVE_LOCK = asyncio.Lock()
_pending = False

DEFAULT_INBOUNDS = []


def act(msg: str, level: str = "info"):
    ACT.append({"msg": msg, "level": level, "t": now().isoformat()})


def allowed(l: Optional[dict]) -> bool:
    if not l or not l.get("active", True):
        return False
    if l.get("vol", 0) > 0 and l.get("used", 0) >= l["vol"]:
        return False
    exp = l.get("exp")
    if exp:
        try:
            if datetime.fromisoformat(exp) < now():
                return False
        except Exception:
            pass
    return True


async def load():
    global _admin, ADMIN_USER
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            for ib in DEFAULT_INBOUNDS:
                INBOUNDS[ib["id"]] = dict(ib)
            return
        async with aiofiles.open(DATA_FILE) as f:
            d = json.loads(await f.read())
        LINKS.update(d.get("links", {}))
        SUBS.update(d.get("subs", {}))
        if d.get("inbounds"):
            INBOUNDS.update(d["inbounds"])
        # WebSocket-only build: keep only WebSocket inbounds.
        INBOUNDS.clear()
        for iid, ib in (d.get("inbounds") or {}).items():
            if (ib.get("network") or "ws").lower() == "ws":
                INBOUNDS[iid] = dict(ib)
        # Drop links bound to removed transports; keep only WebSocket links.
        for lid, lk in list(LINKS.items()):
            ib = INBOUNDS.get(lk.get("inbound_id"))
            if ib is not None and (ib.get("network") or "ws").lower() != "ws":
                LINKS.pop(lid, None)
        if "ah" in d:
            _admin = d["ah"]
        if "settings" in d:
            SETTINGS.update(d["settings"])
        if SETTINGS.get("admin_user"):
            ADMIN_USER = str(SETTINGS["admin_user"]).strip() or ADMIN_USER
        STATS["bytes"] = d.get("bytes", 0)
        STATS["reqs"] = d.get("reqs", 0)
        log.info("loaded %s links %s subs %s inbounds", len(LINKS), len(SUBS), len(INBOUNDS))
    except Exception as e:
        log.warning("load %s", e)
        # No default inbounds are created in the WS-only build.


async def save():
    async with SAVE_LOCK:
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            d = {
                "links": dict(LINKS),
                "subs": dict(SUBS),
                "inbounds": dict(INBOUNDS),
                "ah": _admin,
                "settings": SETTINGS,
                "bytes": STATS["bytes"],
                "reqs": STATS["reqs"],
            }
            tmp = DATA_FILE.with_suffix(".tmp")
            async with aiofiles.open(tmp, "w") as f:
                await f.write(json.dumps(d, ensure_ascii=False, indent=2))
            tmp.replace(DATA_FILE)
        except Exception as e:
            log.warning("save %s", e)


async def schedule_save():
    global _pending
    if _pending:
        return
    _pending = True
    try:
        await asyncio.sleep(1.5)
        await save()
    finally:
        _pending = False


async def new_sess() -> str:
    t = secrets.token_urlsafe(32)
    async with XLOCK:
        SESS[t] = time.time() + TTL
    return t


async def ok_sess(t: Optional[str]) -> bool:
    if not t:
        return False
    async with XLOCK:
        exp = SESS.get(t)
        if not exp or exp < time.time():
            SESS.pop(t, None)
            return False
        return True


async def auth(req: Request):
    if not await ok_sess(req.cookies.get(COOKIE)):
        raise HTTPException(401, "unauthorized")
    return True


def get_inbound(link: dict) -> dict:
    iid = link.get("inbound_id")
    if iid and iid in INBOUNDS:
        return INBOUNDS[iid]
    # legacy fallback
    proto = link.get("proto", "vless")
    for ib in INBOUNDS.values():
        if ib.get("proto") == proto and ib.get("network") == "ws":
            return ib
    return {
        "proto": proto,
        "network": "ws",
        "security": "tls",
        "path": "/ws" if proto == "vless" else f"/{proto}-ws",
    }


def tunnel_path(ib: dict, uid: str) -> str:
    """Path in client share link."""
    proto = ib.get("proto", "vless")
    if proto == "trojan":
        return f"/trojan-ws/{uid}"
    if proto == "ss":
        return f"/ss-ws/{uid}"
    return f"/ws/{uid}"


def share(link: dict, h: Optional[str] = None) -> str:
    """Build share URI from link + its inbound."""
    h = h or host()
    lab = quote(link.get("label") or "LPRW")
    uid = link["id"]
    ib = get_inbound(link)
    proto = ib.get("proto", link.get("proto", "vless"))
    network = ib.get("network", "ws")
    security = ib.get("security", "tls") or "none"
    path = tunnel_path(ib, uid)
    fp = "chrome"
    alpn = "http/1.1"
    sni = h

    if proto == "ss":
        method = link.get("ss_method") or ib.get("ss_method") or "aes-256-gcm"
        password = link.get("ss_password") or uid
        userinfo = base64.urlsafe_b64encode(
            f"{method}:{password}@{h}:443".encode()
        ).decode().rstrip("=")
        mode = "websocket"
        plugin = quote(f"v2ray-plugin;mode={mode};path={path};host={h};tls" + ("" if security == "tls" else ""))
        return f"ss://{userinfo}?plugin={plugin}#{lab}"

    ctype = "ws"
    path_for_client = path
    use_alpn = "http/1.1"

    if proto == "trojan":
        params = {
            "security": security if security != "none" else "none",
            "type": ctype,
            "host": h,
            "path": path_for_client,
        }
        if security == "tls":
            params.update({"sni": sni, "fp": fp, "alpn": use_alpn})
        q = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
        return f"trojan://{uid}@{h}:443?{q}#{lab}"

    params = {
        "encryption": "none",
        "security": security if security != "none" else "none",
        "type": ctype,
        "host": h,
        "path": path_for_client,
    }
    if security == "tls":
        params.update({"sni": sni, "fp": fp, "alpn": use_alpn})
    q = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
    return f"vless://{uid}@{h}:443?{q}#{lab}"


def outbound_configs() -> list[str]:
    raw = SETTINGS.get("outbound_configs") or []
    if not isinstance(raw, list):
        return []
    out = []
    seen = set()
    for item in raw:
        v = str(item or "").strip()
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def subscription_lines(lk: dict, h: str) -> list[str]:
    lines = []
    if not SETTINGS.get("outbound_remove_status", False):
        lines.append(status_line(lk, h))
    if not SETTINGS.get("outbound_remove_primary", False):
        lines.append(share(lk, h))
    if SETTINGS.get("outbound_enabled", False):
        lines.extend(outbound_configs())
    return lines


def subscription_config_lines(lk: dict, h: str) -> list[str]:
    """Only real proxy configs shown in the user portal/copy buttons.
    Subscription metadata such as the usage/status line is intentionally excluded.
    """
    lines = []
    if not SETTINGS.get("outbound_remove_primary", False):
        lines.append(share(lk, h))
    if SETTINGS.get("outbound_enabled", False):
        lines.extend(outbound_configs())
    return lines


def status_line(link: dict, h: str) -> str:
    used = int(link.get("used", 0) or 0)
    vol = int(link.get("vol", 0) or 0)
    left_h = "نامحدود" if vol <= 0 else bh(max(0, vol - used))
    days = "نامحدود"
    exp = link.get("exp")
    if exp:
        try:
            delta = datetime.fromisoformat(exp) - now()
            days = f"{max(0, delta.days)} روز"
        except Exception:
            days = str(exp)[:10]
    label = link.get("label") or "LPRW"
    remark = quote(f"{label} | باقیمانده {left_h} | {days}")
    return (
        f"vless://00000000-0000-0000-0000-000000000001@127.0.0.1:80"
        f"?encryption=none&security=none&type=tcp&headerType=none#{remark}"
    )


def enrich(l: dict, h: str) -> dict:
    o = dict(l)
    o["used_h"] = bh(l.get("used", 0))
    vol = l.get("vol", 0)
    o["vol_h"] = "نامحدود" if vol <= 0 else bh(vol)
    o["pct"] = min(100, int(l.get("used", 0) / vol * 100)) if vol > 0 else 0
    o["ok"] = allowed(l)
    o["share"] = share(l, h)
    o["sub_configs"] = subscription_config_lines(l, h)
    o["online"] = sum(1 for c in CONNECTIONS.values() if c.get("uuid") == l["id"])
    # Link is inactive when its expiry has passed or its traffic allowance is exhausted.
    o["inactive"] = bool(
        (l.get("expiry") and l.get("expiry") < time.time()) or
        (l.get("total") and l.get("total") > 0 and l.get("used", 0) >= l.get("total"))
    )
    # پنل کاربری = همان لینک ساب (مثل پاسارگاد): مرورگر → ظاهر، کلاینت → کانفیگ
    o["user_url"] = f"https://{h}/u/{l['id']}"
    o["qr_url"] = f"https://{h}/qr/{l['id']}"
    o["sub_url"] = f"https://{h}/u/{l['id']}"
    ib = get_inbound(l)
    o["inbound_name"] = ib.get("name", "")
    o["proto"] = ib.get("proto", l.get("proto", "vless"))
    o["network"] = ib.get("network", "ws")
    return o


def find_link(uid: str) -> Optional[dict]:
    if uid in LINKS and allowed(LINKS[uid]):
        return LINKS[uid]
    compact = uid.replace("-", "").lower()
    for lid, lk in LINKS.items():
        if lid.replace("-", "").lower() == compact and allowed(lk):
            return lk
    return None


def on_usage(uid: str, n: int) -> bool:
    STATS["bytes"] += n
    STATS["reqs"] += 1
    HOURLY[time.strftime("%H:00")] += n
    link = LINKS.get(uid)
    if link is None:
        compact = uid.replace("-", "").lower()
        for lid, lk in LINKS.items():
            if lid.replace("-", "").lower() == compact:
                link = lk
                break
    if link is None:
        return False
    if not link.get("active", True):
        return False
    link["used"] = link.get("used", 0) + n
    vol = link.get("vol", 0)
    if vol > 0 and link["used"] >= vol:
        return False
    return True


def reg_conn(uid: str) -> str:
    cid = secrets.token_urlsafe(6)
    CONNECTIONS[cid] = {"uuid": uid, "at": time.time(), "bytes": 0}
    return cid


def unreg_conn(cid: str):
    CONNECTIONS.pop(cid, None)


# ── models ───────────────────────────────────────────────────────────────────

class LoginIn(BaseModel):
    username: str = ""
    password: str


class InboundIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    proto: str = Field(..., pattern="^(vless|trojan|ss)$")
    network: str = Field(default="ws", pattern="^ws$")
    security: str = Field(default="tls", pattern="^(tls|none)$")
    path: str = Field(default="", max_length=120)
    ss_method: str = Field(default="aes-256-gcm")


class LinkIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    inbound_id: str = Field(..., min_length=1)
    volume_gb: float = Field(default=0, ge=0)
    days: int = Field(default=0, ge=0)
    max_conn: int = Field(default=0, ge=0)
    remark: str = Field(default="", max_length=200)


class LinkPatch(BaseModel):
    label: Optional[str] = None
    inbound_id: Optional[str] = None
    volume_gb: Optional[float] = None
    days: Optional[int] = None
    max_conn: Optional[int] = None
    active: Optional[bool] = None
    remark: Optional[str] = None
    reset_usage: Optional[bool] = None


class SubIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    link_ids: list[str] = Field(default_factory=list)
    volume_gb: float = Field(default=0, ge=0)
    days: int = Field(default=0, ge=0)


class SubPatch(BaseModel):
    name: Optional[str] = None
    link_ids: Optional[list[str]] = None
    volume_gb: Optional[float] = None
    days: Optional[int] = None


class SettingsIn(BaseModel):
    panel_name: Optional[str] = None
    admin_user: Optional[str] = Field(default=None, min_length=1, max_length=80)
    announce: Optional[str] = None
    support_url: Optional[str] = None


class OutboundIn(BaseModel):
    enabled: bool
    remove_primary: bool = False
    remove_status: bool = False
    configs: list[str] = Field(default_factory=list, max_length=1000)


class PasswordIn(BaseModel):
    current: str
    new_password: str = Field(..., min_length=4)


app = FastAPI(title="LPRW", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def capture_host(request: Request, call_next):
    try:
        xf = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        hdr = (request.headers.get("host") or "").split(",")[0].strip()
        for raw in (xf, hdr):
            if not raw:
                continue
            h = raw.replace("https://", "").replace("http://", "").split("/")[0].strip()
            if ":" in h and not h.startswith("["):
                host_part, _, port = h.rpartition(":")
                if port in ("80", "443"):
                    h = host_part
            if h and h not in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
                os.environ["PUBLIC_HOST"] = h
                SETTINGS["public_host"] = h
                break
    except Exception:
        pass
    return await call_next(request)


@app.on_event("startup")
async def startup():
    await load()
    act(f"LPRW {VERSION} started", "ok")
    log.info("LPRW %s host=%s", VERSION, host())


@app.on_event("shutdown")
async def shutdown():
    await save()


@app.get("/")
async def root():
    return {"service": "LPRW", "version": VERSION, "host": host(), "status": "active"}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "online": len(CONNECTIONS),
        "links": len(LINKS),
        "inbounds": len(INBOUNDS),
        "uptime": int(time.time() - STATS["start"]),
    }


@app.post("/api/login")
async def login(body: LoginIn, response: Response):
    user_ok = (body.username or "").strip().lower() == ADMIN_USER.lower()
    if not user_ok or hp(body.password) != _admin:
        raise HTTPException(401, "wrong username or password")
    tok = await new_sess()
    response.set_cookie(COOKIE, tok, httponly=True, max_age=TTL, samesite="lax")
    act(f"admin login ({body.username})", "ok")
    return {"ok": True, "user": ADMIN_USER}


@app.post("/api/logout")
async def logout(request: Request, response: Response):
    t = request.cookies.get(COOKIE)
    if t:
        async with XLOCK:
            SESS.pop(t, None)
    response.delete_cookie(COOKIE)
    return {"ok": True}


@app.get("/api/me")
async def me(_: bool = Depends(auth)):
    return {"ok": True, "version": VERSION, "name": SETTINGS.get("panel_name", "LPRW")}


@app.get("/api/stats")
async def stats(request: Request, _: bool = Depends(auth)):
    h = host(request)
    return {
        "bytes": STATS["bytes"],
        "bytes_h": bh(STATS["bytes"]),
        "reqs": STATS["reqs"],
        "online": len(CONNECTIONS),
        "links": len(LINKS),
        "active_links": sum(1 for l in LINKS.values() if allowed(l)),
        "subs": len(SUBS),
        "inbounds": len(INBOUNDS),
        "uptime": int(time.time() - STATS["start"]),
        "uptime_h": (lambda s: f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}")(
            int(time.time() - STATS["start"])
        ),
        "hourly": dict(sorted(HOURLY.items())[-24:]),
        "host": h,
        "public_host": h,
        "version": VERSION,
        "announce": SETTINGS.get("announce", ""),
        "connections": [
            {"id": k, "uuid": v.get("uuid", "")[:8], "sec": int(time.time() - v.get("at", time.time()))}
            for k, v in list(CONNECTIONS.items())[:50]
        ],
    }


@app.get("/api/xray-status")
async def xray_status(_: bool = Depends(auth)):
    """Return the live Xray process state in three dashboard-friendly levels."""
    try:
        xray_bin = shutil.which("xray")
        if not xray_bin:
            return {"level": "bad", "label": "قطع", "running": False, "reason": "xray binary not found"}
        running = False
        try:
            proc = await asyncio.create_subprocess_exec("pgrep", "-x", "xray", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            await proc.communicate()
            running = proc.returncode == 0
        except Exception:
            # Portable fallback: inspect the process list without shell evaluation.
            proc = await asyncio.create_subprocess_exec("ps", "-eo", "comm=", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            out, _ = await proc.communicate()
            running = any(line.strip() == "xray" for line in out.decode(errors="ignore").splitlines())
        if not running:
            return {"level": "bad", "label": "قطع", "running": False}
        # A running process is normal; if the local API has active connections,
        # show a stronger health signal. Otherwise keep the state conservative.
        level = "ok" if len(CONNECTIONS) > 0 or len(INBOUNDS) > 0 else "medium"
        label = "عادی" if level == "ok" else "متوسط"
        return {"level": level, "label": label, "running": True, "connections": len(CONNECTIONS), "inbounds": len(INBOUNDS)}
    except Exception as e:
        return {"level": "bad", "label": "قطع", "running": False, "reason": str(e)}


@app.get("/api/activity")
async def activity(_: bool = Depends(auth)):
    return list(ACT)[::-1][:150]


# ── Inbounds ─────────────────────────────────────────────────────────────────

@app.get("/api/inbounds")
async def list_inbounds(_: bool = Depends(auth)):
    async with ILOCK:
        return list(INBOUNDS.values())


@app.post("/api/inbounds")
async def create_inbound(body: InboundIn, _: bool = Depends(auth)):
    iid = secrets.token_urlsafe(10)
    path = (body.path or "").strip()
    if not path:
        path = f"/{body.proto}-ws"
    if not path.startswith("/"):
        path = "/" + path
    ib = {
        "id": iid,
        "name": body.name,
        "proto": body.proto,
        "network": body.network,
        "security": body.security,
        "path": path,
        "ss_method": body.ss_method if body.proto == "ss" else None,
        "active": True,
        "created": now().isoformat(),
    }
    async with ILOCK:
        INBOUNDS[iid] = ib
    await schedule_save()
    act(f"inbound created: {body.name}", "ok")
    return {"ok": True, "inbound": ib}


@app.delete("/api/inbounds/{iid}")
async def del_inbound(iid: str, _: bool = Depends(auth)):
    async with ILOCK:
        if iid not in INBOUNDS:
            raise HTTPException(404)
        name = INBOUNDS[iid].get("name", "")
        del INBOUNDS[iid]
    await schedule_save()
    act(f"inbound deleted: {name}", "warn")
    return {"ok": True}


# ── Links ────────────────────────────────────────────────────────────────────

@app.get("/api/links")
async def list_links(request: Request, _: bool = Depends(auth)):
    h = host(request)
    async with LLOCK:
        rows = [enrich(l, h) for l in LINKS.values()]
    rows.sort(key=lambda x: x.get("created", ""), reverse=True)
    return rows


@app.post("/api/links")
async def create_link(body: LinkIn, request: Request, _: bool = Depends(auth)):
    if body.inbound_id not in INBOUNDS:
        raise HTTPException(400, "inbound not found")
    ib = INBOUNDS[body.inbound_id]
    lid = str(uuidlib.uuid4())
    vol = int(body.volume_gb * 1024**3) if body.volume_gb > 0 else 0
    exp = (now() + timedelta(days=body.days)).isoformat() if body.days > 0 else None
    link = {
        "id": lid,
        "label": body.label,
        "inbound_id": body.inbound_id,
        "proto": ib.get("proto", "vless"),
        "vol": vol,
        "used": 0,
        "exp": exp,
        "max_conn": body.max_conn,
        "active": True,
        "remark": body.remark,
        "created": now().isoformat(),
    }
    if ib.get("proto") == "ss":
        link["ss_method"] = ib.get("ss_method") or "aes-256-gcm"
        link["ss_password"] = secrets.token_urlsafe(16)
    async with LLOCK:
        LINKS[lid] = link
    await schedule_save()
    act(f"link created: {body.label}", "ok")
    return {"ok": True, "link": enrich(link, host(request))}


@app.patch("/api/links/{lid}")
async def patch_link(lid: str, body: LinkPatch, _: bool = Depends(auth)):
    async with LLOCK:
        if lid not in LINKS:
            raise HTTPException(404)
        l = LINKS[lid]
        if body.label is not None:
            l["label"] = body.label
        if body.inbound_id is not None:
            if body.inbound_id not in INBOUNDS:
                raise HTTPException(400, "inbound not found")
            l["inbound_id"] = body.inbound_id
            l["proto"] = INBOUNDS[body.inbound_id].get("proto", l.get("proto"))
        if body.volume_gb is not None:
            l["vol"] = int(body.volume_gb * 1024**3) if body.volume_gb > 0 else 0
        if body.days is not None:
            l["exp"] = (now() + timedelta(days=body.days)).isoformat() if body.days > 0 else None
        if body.max_conn is not None:
            l["max_conn"] = body.max_conn
        if body.active is not None:
            l["active"] = body.active
        if body.remark is not None:
            l["remark"] = body.remark
        if body.reset_usage:
            l["used"] = 0
    await schedule_save()
    return {"ok": True}


@app.delete("/api/links/{lid}")
async def del_link(lid: str, _: bool = Depends(auth)):
    async with LLOCK:
        if lid not in LINKS:
            raise HTTPException(404)
        lab = LINKS[lid].get("label", "")
        del LINKS[lid]
    await schedule_save()
    act(f"link deleted: {lab}", "warn")
    return {"ok": True}


@app.get("/api/subs")
async def list_subs(request: Request, _: bool = Depends(auth)):
    h = host(request)
    async with SLOCK:
        out = []
        for s in SUBS.values():
            o = dict(s)
            # یک URL برای پنل کاربری + ساب (مرورگر ظاهر، کلاینت کانفیگ)
            o["url"] = f"https://{h}/g/{s['id']}"
            o["portal"] = o["url"]
            o["used_h"] = bh(s.get("used", 0))
            vol = s.get("vol", 0)
            o["vol_h"] = "نامحدود" if vol <= 0 else bh(vol)
            out.append(o)
    return out


@app.post("/api/subs")
async def create_sub(body: SubIn, request: Request, _: bool = Depends(auth)):
    sid = secrets.token_urlsafe(14)
    vol = int(body.volume_gb * 1024**3) if body.volume_gb > 0 else 0
    exp = (now() + timedelta(days=body.days)).isoformat() if body.days > 0 else None
    sub = {
        "id": sid,
        "name": body.name,
        "link_ids": body.link_ids,
        "vol": vol,
        "used": 0,
        "exp": exp,
        "created": now().isoformat(),
    }
    async with SLOCK:
        SUBS[sid] = sub
    await schedule_save()
    act(f"sub created: {body.name}", "ok")
    h = host(request)
    return {
        "ok": True,
        "sub": sub,
        "url": f"https://{h}/g/{sid}",
        "portal": f"https://{h}/g/{sid}",
    }


@app.patch("/api/subs/{sid}")
async def patch_sub(sid: str, body: SubPatch, _: bool = Depends(auth)):
    async with SLOCK:
        if sid not in SUBS:
            raise HTTPException(404)
        s = SUBS[sid]
        if body.name is not None:
            s["name"] = body.name
        if body.link_ids is not None:
            s["link_ids"] = body.link_ids
        if body.volume_gb is not None:
            s["vol"] = int(body.volume_gb * 1024**3) if body.volume_gb > 0 else 0
        if body.days is not None:
            s["exp"] = (now() + timedelta(days=body.days)).isoformat() if body.days > 0 else None
    await schedule_save()
    act(f"sub updated: {sid[:8]}", "ok")
    return {"ok": True}


@app.delete("/api/subs/{sid}")
async def del_sub(sid: str, _: bool = Depends(auth)):
    async with SLOCK:
        if sid not in SUBS:
            raise HTTPException(404)
        del SUBS[sid]
    await schedule_save()
    return {"ok": True}


@app.get("/api/outbound")
async def get_outbound(_: bool = Depends(auth)):
    return {
        "enabled": bool(SETTINGS.get("outbound_enabled", False)),
        "remove_primary": bool(SETTINGS.get("outbound_remove_primary", False)),
        "remove_status": bool(SETTINGS.get("outbound_remove_status", False)),
        "configs": outbound_configs(),
    }


@app.post("/api/outbound")
async def set_outbound(body: OutboundIn, _: bool = Depends(auth)):
    cleaned = []
    seen = set()
    for raw in body.configs:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    SETTINGS["outbound_enabled"] = bool(body.enabled)
    SETTINGS["outbound_remove_primary"] = bool(body.remove_primary)
    SETTINGS["outbound_remove_status"] = bool(body.remove_status)
    SETTINGS["outbound_configs"] = cleaned
    await schedule_save()
    act("outbound settings updated", "ok")
    return {"ok": True, **(await get_outbound(True))}


@app.get("/api/settings")
async def get_set(_: bool = Depends(auth)):
    return SETTINGS


@app.post("/api/settings")
async def set_set(body: SettingsIn, _: bool = Depends(auth)):
    global ADMIN_USER
    data = body.model_dump(exclude_none=True)
    if "admin_user" in data:
        new_user = str(data["admin_user"]).strip()
        if not new_user:
            raise HTTPException(400, "username cannot be empty")
        ADMIN_USER = new_user
        data["admin_user"] = new_user
    SETTINGS.update(data)
    await schedule_save()
    return {"ok": True, "settings": SETTINGS}


@app.post("/api/password")
async def chg_pw(body: PasswordIn, _: bool = Depends(auth)):
    global _admin
    if hp(body.current) != _admin:
        raise HTTPException(400, "wrong current password")
    _admin = hp(body.new_password)
    await schedule_save()
    act("password changed", "ok")
    return {"ok": True}


@app.get("/api/backup")
async def backup(_: bool = Depends(auth)):
    return {
        "links": dict(LINKS),
        "subs": dict(SUBS),
        "inbounds": dict(INBOUNDS),
        "settings": SETTINGS,
        "version": VERSION,
    }


@app.get("/qr/{lid}")
async def qr(lid: str, request: Request):
    async with LLOCK:
        lk = LINKS.get(lid)
        if not lk:
            raise HTTPException(404)
        text = share(lk, host(request))
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


def _wants_html(request: Request) -> bool:
    """مرورگر → HTML ؛ کلاینت ساب → کانفیگ (مثل پاسارگاد)."""
    accept = (request.headers.get("accept") or "").lower()
    ua = (request.headers.get("user-agent") or "").lower()
    # subscription clients
    client_hints = (
        "v2ray", "clash", "sing-box", "singbox", "shadowrocket", "quantumult",
        "stash", "nekobox", "streisand", "hiddify", "surge", "loon", "okhttp",
    )
    if any(x in ua for x in client_hints):
        return False
    if "text/html" in accept and "mozilla" in ua:
        return True
    if not accept or accept == "*/*":
        # بسیاری از کلاینت‌ها Accept خاصی نمی‌فرستند
        if "mozilla" in ua:
            return True
        return False
    return "text/html" in accept and "mozilla" in ua


def _sub_response_for_link(lk: dict, h: str) -> Response:
    lines = subscription_lines(lk, h)
    used = lk.get("used", 0)
    total = lk.get("vol", 0)
    exp = lk.get("exp")
    label = lk.get("label") or "LPRW"
    expire_ts = 0
    if exp:
        try:
            expire_ts = int(datetime.fromisoformat(exp).timestamp())
        except Exception:
            expire_ts = 0
    if not lines:
        raise HTTPException(404, "no configs")
    content = base64.b64encode("\n".join(lines).encode()).decode()
    title_b64 = base64.b64encode(label.encode()).decode()
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "profile-update-interval": "6",
            "profile-title": f"base64:{title_b64}",
            "subscription-userinfo": f"upload=0; download={used}; total={total}; expire={expire_ts}",
        },
    )


@app.get("/u/{lid}")
@app.get("/sub/{lid}")
async def user_page(lid: str, request: Request):
    """ادغام پنل کاربری + ساب: یک لینک برای ظاهر و کانفیگ."""
    async with LLOCK:
        lk = LINKS.get(lid)
        if not lk:
            raise HTTPException(404)
        h = host(request)
        if not _wants_html(request):
            if not allowed(lk):
                raise HTTPException(403, "inactive")
            return _sub_response_for_link(lk, h)
        d = enrich(lk, h)

    from pages import USER_PORTAL

    exp = d.get("exp") or "—"
    if exp and exp != "—":
        exp = exp[:19].replace("T", " ")
    html = (
        USER_PORTAL.replace("{{LABEL}}", d.get("label") or "LPRW")
        .replace("{{STATUS}}", "فعال" if d["ok"] else "غیرفعال")
        .replace("{{STATUS_CLASS}}", "ok" if d["ok"] else "bad")
        .replace("{{USED}}", d["used_h"])
        .replace("{{VOL}}", d["vol_h"])
        .replace("{{PCT}}", str(d["pct"]))
        .replace("{{PROTO}}", (d.get("proto") or "vless").upper())
        .replace("{{ONLINE}}", str(d["online"]))
        .replace("{{EXP}}", exp)
        .replace("{{SHARE}}", d["share"])
        .replace("{{SUB_CONFIGS}}", "\n".join(d.get("sub_configs") or []))
        .replace("{{SUB}}", d["sub_url"])
        .replace("{{QR}}", d["qr_url"])
        .replace("{{REMARK}}", d.get("remark") or "")
        .replace("{{HOST}}", h)
        .replace("{{VERSION}}", VERSION)
    )
    return HTMLResponse(html)


@app.get("/g/{sid}")
@app.get("/sub-group/{sid}")
async def group_portal(sid: str, request: Request):
    """ساب گروهی = پنل کاربری گروهی (مرورگر ظاهر / کلاینت کانفیگ)."""
    async with SLOCK:
        sub = SUBS.get(sid)
        if not sub:
            raise HTTPException(404)
        if sub.get("exp"):
            try:
                if datetime.fromisoformat(sub["exp"]) < now():
                    raise HTTPException(403, "expired")
            except HTTPException:
                raise
            except Exception:
                pass
        h = host(request)
        lines = []
        total_used = 0
        total_vol = 0
        first_lk = None
        async with LLOCK:
            ids = sub.get("link_ids") or list(LINKS.keys())
            for i in ids:
                lk = LINKS.get(i)
                if lk and allowed(lk):
                    if first_lk is None:
                        first_lk = lk
                    lines.extend(subscription_lines(lk, h))
                    total_used += int(lk.get("used", 0) or 0)
                    total_vol += int(lk.get("vol", 0) or 0)

        if not _wants_html(request):
            if not lines:
                raise HTTPException(404, "no configs")
            content = base64.b64encode("\n".join(lines).encode()).decode()
            expire_ts = 0
            if sub.get("exp"):
                try:
                    expire_ts = int(datetime.fromisoformat(sub["exp"]).timestamp())
                except Exception:
                    expire_ts = 0
            title_b64 = base64.b64encode((sub.get("name") or "LPRW").encode()).decode()
            return Response(
                content=content,
                media_type="text/plain; charset=utf-8",
                headers={
                    "profile-update-interval": "6",
                    "profile-title": f"base64:{title_b64}",
                    "subscription-userinfo": f"upload=0; download={total_used}; total={total_vol}; expire={expire_ts}",
                },
            )

    # HTML portal for group
    from pages import USER_PORTAL

    label = sub.get("name") or "LPRW"
    group_configs = []
    seen_group_configs = set()
    async with LLOCK:
        ids = sub.get("link_ids") or list(LINKS.keys())
        for i in ids:
            lk = LINKS.get(i)
            if not lk or not allowed(lk):
                continue
            for cfg in subscription_config_lines(lk, h):
                if cfg not in seen_group_configs:
                    seen_group_configs.add(cfg)
                    group_configs.append(cfg)
    share_txt = group_configs[0] if group_configs else (share(first_lk, h) if first_lk else "")
    pct = min(100, int(total_used / total_vol * 100)) if total_vol > 0 else 0
    exp = sub.get("exp") or "—"
    if exp and exp != "—":
        try:
            exp = exp[:19].replace("T", " ")
        except Exception:
            pass
    html = (
        USER_PORTAL.replace("{{LABEL}}", label)
        .replace("{{STATUS}}", "فعال")
        .replace("{{STATUS_CLASS}}", "ok")
        .replace("{{USED}}", bh(total_used))
        .replace("{{VOL}}", "نامحدود" if total_vol <= 0 else bh(total_vol))
        .replace("{{PCT}}", str(pct))
        .replace("{{PROTO}}", "SUB")
        .replace("{{ONLINE}}", "—")
        .replace("{{EXP}}", str(exp))
        .replace("{{SHARE}}", share_txt)
        .replace("{{SUB_CONFIGS}}", "\n".join(group_configs))
        .replace("{{SUB}}", f"https://{h}/g/{sid}")
        .replace("{{QR}}", f"https://{h}/qr/{first_lk['id']}" if first_lk else "")
        .replace("{{REMARK}}", f"{len(lines)//2} کانفیگ")
        .replace("{{HOST}}", h)
        .replace("{{VERSION}}", VERSION)
    )
    return HTMLResponse(html)


# ── WebSocket tunnels ────────────────────────────────────────────────────────

@app.websocket("/ws/{uid}")
@app.websocket("/vless-ws/{uid}")
async def ws_vless(ws: WebSocket, uid: str):
    await handle_vless_ws(ws, uid, find_link, on_usage, reg_conn, unreg_conn)
    asyncio.create_task(schedule_save())


@app.websocket("/trojan-ws/{uid}")
async def ws_trojan(ws: WebSocket, uid: str):
    def is_ok(u):
        lk = find_link(u)
        return lk if lk and get_inbound(lk).get("proto") == "trojan" else None

    await handle_trojan_ws(ws, uid, is_ok, on_usage, reg_conn, unreg_conn)
    asyncio.create_task(schedule_save())


@app.websocket("/ss-ws/{uid}")
async def ws_ss(ws: WebSocket, uid: str):
    def is_ok(u):
        lk = find_link(u)
        return lk if lk and get_inbound(lk).get("proto") == "ss" else None

    await handle_ss_ws(ws, uid, is_ok, on_usage, reg_conn, unreg_conn)
    asyncio.create_task(schedule_save())


# Dynamic paths for custom inbounds: /{path}/{uid}
def _proto_of(uid: str) -> str:
    lk = find_link(uid) or LINKS.get(uid)
    if not lk:
        return "vless"
    return get_inbound(lk).get("proto") or lk.get("proto") or "vless"


async def _dispatch_tunnel(ws: WebSocket, uid: str):
    """Route by link inbound protocol."""
    proto = (_proto_of(uid) or "vless").lower()
    if proto == "trojan":
        def is_ok(u):
            lk = find_link(u)
            return lk if lk and get_inbound(lk).get("proto") == "trojan" else None
        await handle_trojan_ws(ws, uid, is_ok, on_usage, reg_conn, unreg_conn)
    elif proto == "ss":
        def is_ok(u):
            lk = find_link(u)
            return lk if lk and get_inbound(lk).get("proto") == "ss" else None
        await handle_ss_ws(ws, uid, is_ok, on_usage, reg_conn, unreg_conn)
    else:
        await handle_vless_ws(ws, uid, find_link, on_usage, reg_conn, unreg_conn)
    asyncio.create_task(schedule_save())


@app.get("/debug/auth/{uid}")
async def debug_auth(uid: str):
    """Why a UUID is accepted or rejected for tunnels."""
    raw = LINKS.get(uid)
    if raw is None:
        compact = uid.replace("-", "").lower()
        for lid, lk in LINKS.items():
            if lid.replace("-", "").lower() == compact:
                raw = lk
                uid = lid
                break
    if raw is None:
        return {"ok": False, "reason": "uuid_not_found", "links": len(LINKS)}
    reasons = []
    if not raw.get("active", True):
        reasons.append("disabled")
    if raw.get("vol", 0) > 0 and raw.get("used", 0) >= raw["vol"]:
        reasons.append("quota_exceeded")
    exp = raw.get("exp")
    if exp:
        try:
            if datetime.fromisoformat(exp) < now():
                reasons.append("expired")
        except Exception:
            pass
    ib = get_inbound(raw)
    return {
        "ok": not reasons,
        "uuid": uid,
        "label": raw.get("label"),
        "active": raw.get("active", True),
        "reasons": reasons or ["allowed"],
        "proto": ib.get("proto"),
        "network": ib.get("network"),
        "used": raw.get("used", 0),
        "vol": raw.get("vol", 0),
    }


from pages import DASHBOARD  # noqa: E402


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(DASHBOARD)


@app.get("/panel")
async def panel():
    return RedirectResponse("/dashboard")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info", loop="uvloop")

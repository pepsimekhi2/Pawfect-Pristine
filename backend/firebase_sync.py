"""Firebase Realtime Database write-mirror (best-effort, never blocks main app).

We don't have an admin/service-account credential for the customer's RTDB, so
this module talks to the Firebase REST API anonymously. Whether writes
succeed depends entirely on the rules deployed to that RTDB (see
FIREBASE_RULES.md). All errors are swallowed — MongoDB remains the
source of truth.
"""
import os
import logging
import httpx
from typing import Any, Optional

logger = logging.getLogger(__name__)

FIREBASE_DB_URL = (os.environ.get("FIREBASE_DB_URL") or "").rstrip("/")
FIREBASE_AUTH_TOKEN = os.environ.get("FIREBASE_AUTH_TOKEN") or ""


def _url(path: str) -> str:
    p = path.lstrip("/")
    q = f"?auth={FIREBASE_AUTH_TOKEN}" if FIREBASE_AUTH_TOKEN else ""
    return f"{FIREBASE_DB_URL}/{p}.json{q}"


def enabled() -> bool:
    return bool(FIREBASE_DB_URL)


async def put(path: str, data: Any) -> bool:
    """PUT data at path. Overwrites whatever is there."""
    if not enabled():
        return False
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.put(_url(path), json=data)
            if r.status_code >= 400:
                logger.info(f"Firebase PUT {path} -> {r.status_code} {r.text[:120]}")
                return False
            return True
    except Exception as e:
        logger.info(f"Firebase PUT {path} failed: {e}")
        return False


async def patch(path: str, data: dict) -> bool:
    if not enabled():
        return False
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.patch(_url(path), json=data)
            return r.status_code < 400
    except Exception as e:
        logger.info(f"Firebase PATCH {path} failed: {e}")
        return False


async def delete(path: str) -> bool:
    if not enabled():
        return False
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.delete(_url(path))
            return r.status_code < 400
    except Exception as e:
        logger.info(f"Firebase DELETE {path} failed: {e}")
        return False


def safe_serializable(d: dict) -> dict:
    """Drop fields that mongo/python returns but Firebase shouldn't store."""
    out = {}
    for k, v in d.items():
        if k.startswith("_"):
            continue
        if k in ("password_hash",):
            continue
        # datetimes -> iso strings
        try:
            from datetime import datetime
            if isinstance(v, datetime):
                out[k] = v.isoformat()
                continue
        except Exception:
            pass
        out[k] = v
    return out

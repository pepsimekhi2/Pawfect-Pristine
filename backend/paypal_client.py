"""PayPal Orders v2 REST API client (live / sandbox).

Pure httpx — no SDK. Handles OAuth token caching and create / capture / get order.
"""
import os
import time
import base64
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

PAYPAL_ENV = (os.environ.get("PAYPAL_ENV") or "live").lower().strip()
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "").strip()
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "").strip()

BASE_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_ENV == "sandbox" else "https://api-m.paypal.com"

_token_cache = {"value": None, "exp": 0.0}


def enabled() -> bool:
    return bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)


async def _fetch_token() -> Optional[str]:
    if not enabled():
        return None
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{BASE_URL}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {auth}",
                         "Accept": "application/json"},
            )
        if r.status_code >= 400:
            logger.warning(f"PayPal token failed: {r.status_code} {r.text[:200]}")
            return None
        j = r.json()
        _token_cache["value"] = j["access_token"]
        # Refresh 60s before expiry
        _token_cache["exp"] = time.time() + max(60, int(j.get("expires_in", 3600)) - 60)
        return _token_cache["value"]
    except Exception as e:
        logger.warning(f"PayPal token exception: {e}")
        return None


async def get_access_token() -> Optional[str]:
    if _token_cache["value"] and _token_cache["exp"] > time.time():
        return _token_cache["value"]
    return await _fetch_token()


async def create_order(amount: float, currency: str = "USD",
                       booking_ref: Optional[str] = None,
                       description: Optional[str] = None) -> dict:
    """Create a PayPal order with CAPTURE intent. Returns the order JSON
    (must include `id` and approval `links`). Raises HTTPError on failure."""
    token = await get_access_token()
    if not token:
        raise RuntimeError("PayPal not configured or token request failed.")
    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": (booking_ref or "default")[:255],
            "description": (description or "Pawfect & Pristine booking")[:127],
            "amount": {"currency_code": currency, "value": f"{round(float(amount), 2):.2f}"},
        }],
        "application_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
            "brand_name": "Pawfect & Pristine",
        },
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{BASE_URL}/v2/checkout/orders",
            json=body,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json",
                     "PayPal-Request-Id": f"booking-{booking_ref or int(time.time()*1000)}"},
        )
    if r.status_code >= 400:
        logger.warning(f"PayPal create_order failed: {r.status_code} {r.text[:400]}")
        raise RuntimeError(f"PayPal create order failed ({r.status_code}): {r.text[:200]}")
    return r.json()


async def capture_order(order_id: str) -> dict:
    """Capture an approved order. Returns the capture JSON.
    `status` should be COMPLETED on success."""
    token = await get_access_token()
    if not token:
        raise RuntimeError("PayPal not configured or token request failed.")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/v2/checkout/orders/{order_id}/capture",
            json={},
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json",
                     "PayPal-Request-Id": f"cap-{order_id}"},
        )
    if r.status_code >= 400:
        logger.warning(f"PayPal capture_order failed: {r.status_code} {r.text[:400]}")
        raise RuntimeError(f"PayPal capture failed ({r.status_code}): {r.text[:200]}")
    return r.json()


async def get_order(order_id: str) -> dict:
    token = await get_access_token()
    if not token:
        raise RuntimeError("PayPal not configured.")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{BASE_URL}/v2/checkout/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    if r.status_code >= 400:
        raise RuntimeError(f"PayPal get_order failed ({r.status_code}): {r.text[:200]}")
    return r.json()

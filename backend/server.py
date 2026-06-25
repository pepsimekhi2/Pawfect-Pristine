from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import re
import logging
import uuid
import httpx
import html
from urllib.parse import quote_plus
from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal, List
from datetime import datetime, timezone, timedelta

from auth_utils import (
    hash_password, verify_password, create_access_token, decode_token, extract_token
)
from pricing import compute_quote, get_public_catalog, SERVICE_CATALOG, generate_time_slots, is_time_in_window, BOOKING_TIME_MIN, BOOKING_TIME_MAX, get_service_duration, hhmm_to_minutes, window_minutes
from tos import TOS_TEXT, TOS_VERSION, TOS_EFFECTIVE
import firebase_sync as fb
import paypal_client as pp
import asyncio

mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ['DB_NAME']]

OWNER_EMAIL = os.environ.get('OWNER_EMAIL', 'hello@pawfectpristine.com')
ORIGIN_LAT = float(os.environ.get('ORIGIN_LAT', '33.7748'))
ORIGIN_LON = float(os.environ.get('ORIGIN_LON', '-84.2963'))
ORIGIN_LABEL = os.environ.get('ORIGIN_LABEL', 'Decatur, GA')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
ADMIN_PASSPHRASE = os.environ.get('ADMIN_PASSPHRASE', 'duck')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
RESEND_FROM = os.environ.get('RESEND_FROM', 'Pawfect & Pristine <bookings@pawfectpristine.xyz>')
BREVO_FORM_URL = os.environ.get(
    'BREVO_FORM_URL',
    'https://d9cf8a8a.sibforms.com/serve/MUIFAPON8oiNFYtLkSZQDsRYsOuTwKHAkQulhC03ZdbGNA7bcWU6PnPZmnHb-O8tyxVT-M4HaU3S2FRcBBEQj0sfZ28J8dgJsw7RY6SFoieSfGdCFefSoLD3h0zw5s6voHCsGXWJwuKfFidda3Ne_1o1MjkzpsPovwLjRsQLtRh6bFjl9g-xqn58FsDFXuQ2_Q0luHTmCTET-cARwA=='
)

app = FastAPI()
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============= Models =============
class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    marketing_opt_in: bool = False


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str = "customer"


class ETARequest(BaseModel):
    address: str


class QuotePayload(BaseModel):
    service_value: str
    tier_key: Optional[str] = None
    preferred_date: Optional[str] = None  # ISO date string
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    pet_count: Optional[int] = None
    addons: list[str] = []
    discounts: list[str] = []


class BookingCreate(BaseModel):
    name: str
    phone: str
    address: str
    service_value: str  # internal key e.g. general_cleaning
    tier_key: Optional[str] = None
    pets: int = 0
    notes: str = ""
    preferred_date: str = ""   # ISO date e.g. 2026-02-14
    preferred_time: str = ""   # "14:00"
    payment_plan: Literal["pay_later", "half_now", "all_now"] = "pay_later"
    payment_method: Literal["card", "cash", "later", "paypal"] = "later"
    tos_accepted: bool = True
    access_method: Literal["home", "lockbox", "hidden_key", "garage_code", "doorman", "other"] = "home"
    access_notes: str = ""
    # ── Upsell questionnaire ──
    property_type: Optional[str] = None        # "house" | "apartment" | "business"
    bedrooms: Optional[int] = None              # cleaning only
    bathrooms: Optional[int] = None             # cleaning only
    pet_count: Optional[int] = None             # pet services only
    addons: list[str] = []                       # ["inside_fridge", "baseboards", ...]
    discounts: list[str] = []                    # ["byo_supplies"]
    # ── PayPal capture (set when paid via card/PayPal on site) ──
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    paypal_captured_amount: Optional[float] = None



class RescheduleBody(BaseModel):
    preferred_date: str
    preferred_time: str


class StatusBody(BaseModel):
    status: Literal["scheduled", "on_the_way", "in_progress", "completed", "cancelled"]


# ============= Helpers =============
async def get_current_user(request: Request) -> dict:
    token = extract_token(request)
    payload = decode_token(token)
    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user.pop("password_hash", None)
    user.pop("_id", None)
    return user


async def maybe_current_user(request: Request) -> Optional[dict]:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def geocode_nominatim(address: str) -> Optional[dict]:
    """Geocode via Nominatim with a Mongo cache. Free public API gets
    rate-limited so caching is essential for reliability."""
    key = (address or "").strip().lower()
    if not key:
        return None
    try:
        cached = await db.geocode_cache.find_one({"_id": key})
    except Exception:
        cached = None
    if cached and cached.get("lat") is not None:
        return {"lat": cached["lat"], "lon": cached["lon"], "display_name": cached.get("display_name", address)}
    if cached and cached.get("miss"):
        return None
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": "us"}
    headers = {"User-Agent": "PawfectPristine/1.0 (booking@pawfectpristine.xyz)"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params, headers=headers)
        if r.status_code != 200:
            logger.warning(f"Nominatim geocode status {r.status_code} for {address!r}")
            return None
        data = r.json()
    except Exception as e:
        logger.warning(f"Nominatim geocode failed for {address!r}: {e}")
        return None
    if not data:
        try:
            await db.geocode_cache.update_one(
                {"_id": key},
                {"$set": {"miss": True, "cached_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
        except Exception:
            pass
        return None
    out = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "display_name": data[0]["display_name"]}
    try:
        await db.geocode_cache.update_one(
            {"_id": key},
            {"$set": {**out, "cached_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    except Exception:
        pass
    return out


async def address_suggest_photon(query: str, limit: int = 6) -> list[dict]:
    """Autocomplete addresses via OpenStreetMap Nominatim. Free, no key.
    (Originally tried Photon but Photon's host is blocked from this network.)
    Biased to GA / metro Atlanta. Returns simplified list."""
    q = (query or "").strip()
    if len(q) < 3:
        return []
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q,
        "format": "json",
        "limit": limit,
        "countrycodes": "us",
        "addressdetails": 1,
        # Bias to a generous box around Decatur/Atlanta:
        "viewbox": "-85.5,34.6,-83.2,32.8",
        "bounded": 0,
    }
    headers = {"User-Agent": "PawfectPristine/1.0 (booking@pawfectpristine.local)"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url, params=params, headers=headers)
        if r.status_code != 200:
            logger.warning(f"Nominatim suggest status {r.status_code}")
            return []
        rows = r.json() or []
    except Exception as e:
        logger.warning(f"Nominatim suggest failed: {e}")
        return []
    out = []
    seen = set()
    for row in rows:
        try:
            lat = float(row.get("lat"))
            lon = float(row.get("lon"))
        except Exception:
            continue
        addr = row.get("address") or {}
        # Skip if state is not in GA neighbour box (Nominatim doesn't strict-filter)
        state = (addr.get("state") or "")
        if state and state not in {"Georgia", "Alabama", "South Carolina", "Tennessee", "Florida", "North Carolina"}:
            # Still allow if no state info
            continue
        parts = []
        if addr.get("house_number") and addr.get("road"):
            parts.append(f"{addr['house_number']} {addr['road']}")
        elif addr.get("road"):
            parts.append(addr["road"])
        elif row.get("name"):
            parts.append(row.get("name"))
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet") or addr.get("suburb")
        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if addr.get("postcode"):
            parts.append(addr["postcode"])
        label = ", ".join([p for p in parts if p])
        if not label:
            label = row.get("display_name", "").split(",")[:4]
            label = ", ".join(label) if isinstance(label, list) else label
        if not label or label in seen:
            continue
        seen.add(label)
        out.append({
            "label": label,
            "address": label,
            "lat": lat,
            "lon": lon,
            "type": row.get("type"),
        })
        if len(out) >= limit:
            break
    return out


async def osrm_route(o_lat, o_lon, d_lat, d_lon) -> Optional[dict]:
    url = f"https://router.project-osrm.org/route/v1/driving/{o_lon},{o_lat};{d_lon},{d_lat}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, params={"overview": "false"})
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        route = data["routes"][0]
        return {"distance_meters": route["distance"], "duration_seconds": route["duration"]}


def classify_zone(miles: float) -> dict:
    if miles <= 7:
        return {"zone": "standard", "extra_fee": 0, "zone_label": "Standard Service Area",
                "zone_message": "You're right in our happy zone — no extra fees!"}
    if miles <= 13:
        return {"zone": "extended", "extra_fee": 10, "zone_label": "Extended Service Area",
                "zone_message": "We can swing by — a small $10 travel fee applies."}
    return {"zone": "out_of_range", "extra_fee": 0, "zone_label": "Out of Range",
            "zone_message": "You're a bit far for our regular routes. Call us at (470) 381-4682 for a custom quote!"}


def format_arrival(duration_minutes: float):
    now = datetime.now(timezone.utc) - timedelta(hours=5)
    arrival = now + timedelta(minutes=duration_minutes + 15)
    window_end = arrival + timedelta(minutes=20)
    def fmt(dt):
        h = dt.hour % 12 or 12
        suffix = "AM" if dt.hour < 12 else "PM"
        return f"{h}:{dt.minute:02d} {suffix}"
    return fmt(arrival), f"{fmt(arrival)} – {fmt(window_end)}"


def send_owner_sms(body: str) -> bool:
    """Twilio removed — booking owner notifications now go via email."""
    return False


async def subscribe_to_brevo(email: str) -> bool:
    if not BREVO_FORM_URL:
        return False
    form_data = {
        "EMAIL": email,
        "email_address_check": "",
        "locale": "en",
        "html_type": "simple",
    }
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.post(
                BREVO_FORM_URL,
                data=form_data,
                headers={"User-Agent": "PawfectPristine/1.0"},
            )
        if response.status_code >= 400:
            logger.warning(f"Brevo signup failed for {email}: {response.status_code} {response.text[:120]}")
            return False
        return True
    except Exception as e:
        logger.warning(f"Brevo signup failed for {email}: {e}")
        return False


def welcome_offer_html(name: str) -> str:
    safe_name = html.escape(name.strip() or "there")
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;line-height:1.65;color:#1f2a24;max-width:560px;margin:0 auto;padding:24px;background:#fdf9f5;border-radius:14px;border:1px solid #e6efe9">
      <div style="font-family:Georgia,serif;font-size:26px;color:#1e3a2f;margin-bottom:8px">🐾 Welcome, {safe_name}.</div>
      <p style="margin:14px 0;font-size:15px">Thanks for joining <strong>Pawfect &amp; Pristine</strong>. Your first booking gets <strong style="color:#3d7a5c">25% off</strong> automatically — no code needed.</p>
      <p style="margin:14px 0;font-size:15px">When you’re ready, head to <a href="https://www.pawfectpristine.xyz/book" style="color:#3d7a5c;font-weight:600">pawfectpristine.xyz/book</a> and your discount will appear in your running total before checkout.</p>
      <p style="margin:24px 0 6px 0;font-size:13px;color:#5f6f67">– Mekhi &amp; the Pawfect &amp; Pristine team</p>
      <p style="font-size:11px;color:#8a9890;margin-top:18px">You can unsubscribe from promotional emails any time.</p>
    </div>
    """


def booking_confirmation_html(booking: dict) -> str:
    name = html.escape(booking.get("name", "there"))
    svc = html.escape(booking.get("service_label", "your service"))
    tier = html.escape(booking.get("tier_label") or "")
    when_date = html.escape(booking.get("preferred_date") or "")
    when_time = html.escape(booking.get("preferred_time") or "")
    addr = html.escape(booking.get("address", ""))
    total = booking.get("grand_total", 0)
    due_now = booking.get("due_now", 0)
    due_later = booking.get("due_later", 0)
    paid_status = booking.get("payment_status", "unpaid")
    paid_chip = {
        "paid_full": '<span style="background:#3d7a5c;color:#fff;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600">PAID IN FULL</span>',
        "paid_half": '<span style="background:#d4a435;color:#1e3a2f;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600">HALF PAID</span>',
        "unpaid": '<span style="background:#eef7f2;color:#3d7a5c;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600">PAY ON ARRIVAL</span>',
    }.get(paid_status, "")
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;line-height:1.65;color:#1f2a24;max-width:560px;margin:0 auto;padding:0">
      <div style="background:linear-gradient(135deg,#1e3a2f 0%,#3d7a5c 100%);color:#fff;padding:28px 26px;border-radius:14px 14px 0 0">
        <div style="font-size:13px;letter-spacing:2px;text-transform:uppercase;opacity:.85">Booking confirmed</div>
        <div style="font-family:Georgia,serif;font-size:30px;margin-top:8px">You’re booked, {name} 🐾</div>
      </div>
      <div style="background:#fdf9f5;padding:24px 26px;border:1px solid #e6efe9;border-top:0;border-radius:0 0 14px 14px">
        <div style="font-size:15px;margin-bottom:18px">Here’s the recap. We’ll text/email you if anything changes.</div>
        <table style="width:100%;font-size:14px;border-collapse:collapse">
          <tr><td style="padding:6px 0;color:#5f6f67;width:130px">Service</td><td style="padding:6px 0"><strong>{svc}</strong>{(' · ' + tier) if tier else ''}</td></tr>
          <tr><td style="padding:6px 0;color:#5f6f67">When</td><td style="padding:6px 0"><strong>{when_date}</strong>{(' at ' + when_time) if when_time else ''}</td></tr>
          <tr><td style="padding:6px 0;color:#5f6f67">Where</td><td style="padding:6px 0">{addr}</td></tr>
          <tr><td colspan="2" style="padding:10px 0"><hr style="border:none;border-top:1px solid #e6efe9"/></td></tr>
          <tr><td style="padding:6px 0;color:#5f6f67">Total</td><td style="padding:6px 0;font-family:Georgia,serif;font-size:22px;color:#1e3a2f"><strong>${total:.2f}</strong></td></tr>
          <tr><td style="padding:6px 0;color:#5f6f67">Paid today</td><td style="padding:6px 0">${due_now:.2f} {paid_chip}</td></tr>
          <tr><td style="padding:6px 0;color:#5f6f67">Due on arrival</td><td style="padding:6px 0">${due_later:.2f}</td></tr>
        </table>
        <div style="margin-top:22px;font-size:13px;color:#5f6f67">Need to change anything? Visit your <a href="https://www.pawfectpristine.xyz/dashboard" style="color:#3d7a5c;font-weight:600">dashboard</a> or just reply to this email.</div>
        <div style="margin-top:14px;font-size:12px;color:#8a9890">— Mekhi &amp; the Pawfect &amp; Pristine team · (470) 381-4682</div>
      </div>
    </div>
    """


def owner_booking_html(booking: dict) -> str:
    name = html.escape(booking.get("name", ""))
    phone = html.escape(booking.get("phone", ""))
    svc = html.escape(booking.get("service_label", ""))
    tier = html.escape(booking.get("tier_label") or "")
    when_date = html.escape(booking.get("preferred_date") or "")
    when_time = html.escape(booking.get("preferred_time") or "")
    addr = html.escape(booking.get("address", ""))
    notes = html.escape(booking.get("notes") or "")
    access = html.escape(booking.get("access_method", ""))
    access_notes = html.escape(booking.get("access_notes") or "")
    total = booking.get("grand_total", 0)
    due_now = booking.get("due_now", 0)
    pp_id = html.escape(booking.get("paypal_order_id") or "—")
    status = booking.get("payment_status", "unpaid")
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;line-height:1.6;color:#1f2a24">
      <h2 style="margin-bottom:6px">🐾 New booking · ${total:.2f}</h2>
      <div style="color:#5f6f67;font-size:13px;margin-bottom:14px">{status.upper()} · paid today ${due_now:.2f}</div>
      <table style="font-size:14px;border-collapse:collapse">
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">Customer</td><td><strong>{name}</strong> · <a href="tel:{phone}">{phone}</a></td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">Service</td><td>{svc}{(' · ' + tier) if tier else ''}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">When</td><td>{when_date} {when_time}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">Address</td><td>{addr}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">Access</td><td>{access}{(' — ' + access_notes) if access_notes else ''}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">Notes</td><td>{notes or '—'}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#5f6f67">PayPal order</td><td><code>{pp_id}</code></td></tr>
      </table>
    </div>
    """


async def send_resend_email(to_email, subject: str, html_body: str, reply_to: Optional[str] = None) -> bool:
    """Send a transactional email via Resend. `to_email` can be a str or list."""
    if not RESEND_API_KEY:
        logger.info("Resend not configured — skipping email")
        return False
    if isinstance(to_email, str):
        to_list = [to_email]
    else:
        to_list = list(to_email)
    payload = {
        "from": RESEND_FROM,
        "to": to_list,
        "subject": subject,
        "html": html_body,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                         "Content-Type": "application/json"},
            )
        if response.status_code >= 400:
            logger.warning(f"Resend email failed for {to_list}: {response.status_code} {response.text[:240]}")
            return False
        logger.info(f"Resend email sent to {to_list} · subject={subject!r}")
        return True
    except Exception as e:
        logger.warning(f"Resend email failed for {to_list}: {e}")
        return False


async def is_first_time_customer(user: Optional[dict]) -> bool:
    if not user:
        return False
    existing = await db.bookings.find_one(
        {"user_id": user["id"], "status": {"$ne": "cancelled"}},
        {"_id": 1},
    )
    return existing is None


async def check_brute_force(identifier: str):
    rec = await db.login_attempts.find_one({"identifier": identifier})
    if rec and rec.get("count", 0) >= 5:
        locked_until = rec.get("locked_until")
        if locked_until:
            # Mongo returns naive UTC datetimes; normalize for safe comparison.
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > datetime.now(timezone.utc):
                mins = max(1, int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60))
                raise HTTPException(status_code=429, detail=f"Too many attempts. Try again in {mins} min.")


async def record_failed_login(identifier: str):
    rec = await db.login_attempts.find_one({"identifier": identifier})
    count = (rec.get("count", 0) if rec else 0) + 1
    locked_until = datetime.now(timezone.utc) + timedelta(minutes=15) if count >= 5 else None
    await db.login_attempts.update_one(
        {"identifier": identifier},
        {"$set": {"count": count, "locked_until": locked_until, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


async def clear_attempts(identifier: str):
    await db.login_attempts.delete_one({"identifier": identifier})


async def get_blocked_minutes_for_date(date_iso: str, exclude_booking_id: Optional[str] = None) -> set:
    """Return set of all minute-of-day values blocked by existing bookings on that date.
    Honors each booking's service duration."""
    query = {
        "preferred_date": date_iso,
        "status": {"$nin": ["cancelled", "completed"]},
    }
    if exclude_booking_id:
        query["id"] = {"$ne": exclude_booking_id}
    docs = await db.bookings.find(
        query,
        {"_id": 0, "preferred_time": 1, "service_value": 1, "tier_key": 1, "duration_minutes": 1},
    ).to_list(500)
    blocked = set()
    for d in docs:
        t = d.get("preferred_time")
        if not t:
            continue
        try:
            start = hhmm_to_minutes(t)
        except Exception:
            continue
        dur = d.get("duration_minutes") or get_service_duration(d.get("service_value"), d.get("tier_key"))
        for m in range(start, start + dur, 30):
            blocked.add(m)
    return blocked


def slot_conflicts(start_min: int, duration_min: int, blocked: set) -> bool:
    """True if any 30-min step within [start, start+duration) overlaps a blocked minute."""
    for m in range(start_min, start_min + duration_min, 30):
        if m in blocked:
            return True
    return False


def _to_user_out(user: dict) -> UserOut:
    return UserOut(
        id=user["id"], name=user["name"], email=user["email"],
        phone=user.get("phone"), role=user.get("role", "customer"),
    )


# ============= Auth Routes =============
@auth_router.post("/register")
async def register(payload: RegisterPayload, request: Request, response: Response):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if not re.match(r"^[A-Za-z0-9\s'\-\.]{2,80}$", payload.name.strip()):
        raise HTTPException(status_code=400, detail="Please enter a valid name.")
    if not payload.marketing_opt_in:
        raise HTTPException(status_code=400, detail="Please agree to receive promotional emails to create an account.")

    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")

    user_doc = {
        "id": str(uuid.uuid4()),
        "name": payload.name.strip(),
        "email": email,
        "phone": (payload.phone or "").strip() or None,
        "password_hash": hash_password(payload.password),
        "role": "customer",
        "marketing_opt_in": True,
        "marketing_opt_in_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user_doc)
    # Best-effort Firebase mirror
    asyncio.create_task(fb.put(f"users/{user_doc['id']}", fb.safe_serializable({
        **user_doc, "password_hash": None,
    })))
    asyncio.create_task(subscribe_to_brevo(email))
    asyncio.create_task(send_resend_email(
        email,
        "Your 25% off first-booking offer",
        welcome_offer_html(user_doc["name"]),
    ))
    token = create_access_token(user_doc["id"], email)
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax",
                        max_age=60 * 60 * 24 * 7, path="/")
    return {"user": _to_user_out(user_doc).model_dump(), "token": token}


@auth_router.post("/login")
async def login(payload: LoginPayload, request: Request, response: Response):
    email = payload.email.lower().strip()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    await check_brute_force(identifier)

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        await record_failed_login(identifier)
        raise HTTPException(status_code=401, detail="Wrong email or password.")

    await clear_attempts(identifier)
    token = create_access_token(user["id"], email)
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax",
                        max_age=60 * 60 * 24 * 7, path="/")
    return {"user": _to_user_out(user).model_dump(), "token": token}


@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": _to_user_out(user).model_dump()}


class AdminPassphrasePayload(BaseModel):
    passphrase: str


@auth_router.post("/admin-passphrase")
async def admin_passphrase_login(payload: AdminPassphrasePayload, request: Request, response: Response):
    """Quick-access admin login via a shared passphrase (e.g. 'duck').
    Brute-force protected. Returns the seeded admin's JWT on success."""
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:admin-passphrase"
    await check_brute_force(identifier)

    submitted = (payload.passphrase or "").strip()
    if not submitted or submitted.lower() != (ADMIN_PASSPHRASE or "").strip().lower():
        await record_failed_login(identifier)
        raise HTTPException(status_code=401, detail="Incorrect passphrase.")

    if not ADMIN_EMAIL:
        raise HTTPException(status_code=500, detail="Admin not configured.")
    admin = await db.users.find_one({"email": ADMIN_EMAIL.lower(), "role": "admin"})
    if not admin:
        raise HTTPException(status_code=500, detail="Admin user missing — restart backend to reseed.")

    await clear_attempts(identifier)
    token = create_access_token(admin["id"], admin["email"])
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax",
                        max_age=60 * 60 * 24 * 7, path="/")
    return {"user": _to_user_out(admin).model_dump(), "token": token}


# ============= Public/General Routes =============
@api_router.get("/")
async def root():
    return {"message": "Pawfect & Pristine API ready"}


@api_router.get("/catalog")
async def catalog():
    return get_public_catalog()


@api_router.post("/quote")
async def quote(payload: QuotePayload, request: Request):
    user = await maybe_current_user(request)
    first_time_customer = await is_first_time_customer(user)
    q = compute_quote(
        payload.service_value, payload.tier_key, payload.preferred_date,
        property_type=payload.property_type,
        bedrooms=payload.bedrooms,
        bathrooms=payload.bathrooms,
        pet_count=payload.pet_count,
        addon_keys=payload.addons,
        discount_keys=payload.discounts,
        first_time_customer=first_time_customer,
    )
    return q


@api_router.post("/eta")
async def calculate_eta(payload: ETARequest):
    addr = payload.address.strip()
    if not addr:
        raise HTTPException(status_code=400, detail="Address required")
    geo = await geocode_nominatim(addr)
    if not geo:
        raise HTTPException(status_code=404, detail="We couldn't find that address. Try including city + state.")
    route = await osrm_route(ORIGIN_LAT, ORIGIN_LON, geo["lat"], geo["lon"])
    if not route:
        raise HTTPException(status_code=502, detail="Routing service unavailable. Try again.")
    miles = round(route["distance_meters"] / 1609.34, 2)
    mins = round(route["duration_seconds"] / 60, 1)
    zone_info = classify_zone(miles)
    arrival, window = format_arrival(mins)
    return {
        "address": addr, "resolved_address": geo["display_name"],
        "distance_miles": miles, "duration_minutes": mins,
        "arrival_time": arrival, "arrival_window": window, **zone_info,
    }


@api_router.get("/geocode/suggest")
async def geocode_suggest(q: str, limit: int = 6):
    """Autocomplete suggestions for an address input (biased to Decatur, GA).
    Returns at most `limit` US results from Photon (OSM)."""
    suggestions = await address_suggest_photon(q, limit=min(max(1, limit), 10))
    return {"q": q, "results": suggestions}


# ============= Booking Routes =============
@api_router.post("/bookings")
async def create_booking(payload: BookingCreate, user: dict = Depends(get_current_user)):

    if not payload.tos_accepted:
        raise HTTPException(status_code=400, detail="You must accept the Terms of Service.")

    if payload.service_value not in SERVICE_CATALOG:
        raise HTTPException(status_code=400, detail="Unknown service.")

    # Validate time window (9:00 AM – 6:30 PM)
    if payload.preferred_time and not is_time_in_window(payload.preferred_time):
        raise HTTPException(
            status_code=400,
            detail=f"Bookings are only available between {BOOKING_TIME_MIN} and {BOOKING_TIME_MAX}."
        )

    # Address is required + must geocode + must be in service area
    addr_clean = (payload.address or "").strip()
    if not addr_clean:
        raise HTTPException(status_code=400, detail="Service address is required.")
    geo = await geocode_nominatim(addr_clean)
    if not geo:
        raise HTTPException(status_code=400, detail="We couldn't find that address. Try including city + state.")
    route = await osrm_route(ORIGIN_LAT, ORIGIN_LON, geo["lat"], geo["lon"])
    if not route:
        raise HTTPException(status_code=502, detail="Routing service unavailable right now. Try again in a moment.")
    miles = round(route["distance_meters"] / 1609.34, 2)
    mins = round(route["duration_seconds"] / 60, 1)
    z = classify_zone(miles)
    if z["zone"] == "out_of_range":
        raise HTTPException(
            status_code=400,
            detail=f"Sorry — {addr_clean} is {miles} mi from Decatur, outside our service area. Call (470) 381-4682 for a custom quote.",
        )
    eta_dict = {"distance_miles": miles, "duration_minutes": mins,
                "zone": z["zone"], "extra_fee": z["extra_fee"]}

    # Determine duration & validate availability via overlap check
    duration_min = get_service_duration(payload.service_value, payload.tier_key)
    if payload.preferred_date and payload.preferred_time:
        try:
            start_min = hhmm_to_minutes(payload.preferred_time)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid time.")
        # Service must fit before the close-of-day window
        _wmin_start, wmin_end = window_minutes()
        if start_min + duration_min > wmin_end + 30:  # allow last slot to end up to 30 min after max
            raise HTTPException(
                status_code=400,
                detail=f"This service needs {duration_min} min. Pick an earlier time — we close at {BOOKING_TIME_MAX}."
            )
        blocked = await get_blocked_minutes_for_date(payload.preferred_date)
        if slot_conflicts(start_min, duration_min, blocked):
            raise HTTPException(
                status_code=409,
                detail="That time slot overlaps another booking. Please pick a different time."
            )

    first_time_customer = await is_first_time_customer(user)
    quote_data = compute_quote(
        payload.service_value, payload.tier_key, payload.preferred_date,
        property_type=payload.property_type,
        bedrooms=payload.bedrooms,
        bathrooms=payload.bathrooms,
        pet_count=payload.pet_count,
        addon_keys=payload.addons,
        discount_keys=payload.discounts,
        first_time_customer=first_time_customer,
    )

    travel_fee = eta_dict["extra_fee"] if eta_dict else 0
    grand_total = round(quote_data["total"] + travel_fee, 2)

    # Compute "amount due now" based on payment plan
    if payload.payment_plan == "all_now":
        due_now = grand_total
    elif payload.payment_plan == "half_now":
        due_now = round(grand_total / 2, 2)
    else:
        due_now = 0
    due_later = round(grand_total - due_now, 2)

    # Compute payment_status — favor real PayPal capture proof when present
    paid_via_paypal = bool(payload.paypal_capture_id) and payload.payment_method == "paypal"
    if paid_via_paypal:
        if payload.payment_plan == "all_now":
            payment_status = "paid_full"
        elif payload.payment_plan == "half_now":
            payment_status = "paid_half"
        else:
            payment_status = "paid_full"  # shouldn't happen but be safe
    elif payload.payment_method == "paypal":
        # PayPal selected but no capture id (legacy / hosted button) → pending verify
        payment_status = (
            "paid_full_pending_verify" if payload.payment_plan == "all_now"
            else "paid_half_pending_verify" if payload.payment_plan == "half_now"
            else "unpaid"
        )
    else:
        payment_status = "unpaid"

    booking = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": payload.name,
        "phone": payload.phone,
        "address": payload.address,
        "service_value": payload.service_value,
        "service_label": quote_data["service_label"],
        "tier_key": payload.tier_key,
        "tier_label": quote_data["tier_label"],
        "pets": payload.pets,
        "notes": payload.notes,
        "access_method": payload.access_method,
        "access_notes": payload.access_notes,
        "property_type": payload.property_type,
        "bedrooms": payload.bedrooms,
        "bathrooms": payload.bathrooms,
        "pet_count": payload.pet_count,
        "addons": payload.addons,
        "discounts": payload.discounts,
        "preferred_date": payload.preferred_date,
        "preferred_time": payload.preferred_time,
        "duration_minutes": duration_min,
        "quote": quote_data,
        "travel_fee": travel_fee,
        "grand_total": grand_total,
        "due_now": due_now,
        "due_later": due_later,
        "payment_plan": payload.payment_plan,
        "payment_method": payload.payment_method,
        "payment_status": payment_status,
        "paypal_order_id": payload.paypal_order_id,
        "paypal_capture_id": payload.paypal_capture_id,
        "paypal_captured_amount": payload.paypal_captured_amount,
        "status": "scheduled",
        "eta": eta_dict,
        "tos_accepted": True,
        "tos_accepted_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    booking["sms_sent"] = False

    booking["sms_sent"] = False  # legacy field — kept for compatibility

    await db.bookings.insert_one(booking)

    # ── Notifications ──
    # 1) Customer confirmation
    customer_email = None
    if user and user.get("email"):
        customer_email = user["email"]
    if customer_email:
        asyncio.create_task(send_resend_email(
            customer_email,
            f"Booking confirmed — {quote_data['service_label']} on {payload.preferred_date}",
            booking_confirmation_html(booking),
        ))
    # 2) Owner notification
    if OWNER_EMAIL:
        asyncio.create_task(send_resend_email(
            OWNER_EMAIL,
            f"🐾 New booking · ${booking['grand_total']:.2f} · {payload.name}",
            owner_booking_html(booking),
            reply_to=customer_email,
        ))

    # Best-effort Firebase mirror — never blocks
    asyncio.create_task(fb.put(f"bookings/{booking['id']}", fb.safe_serializable(booking)))
    if booking["user_id"]:
        asyncio.create_task(fb.put(
            f"user_bookings/{booking['user_id']}/{booking['id']}",
            fb.safe_serializable({k: booking[k] for k in (
                "id", "service_label", "tier_label", "preferred_date", "preferred_time",
                "status", "grand_total", "due_now", "due_later", "payment_status",
                "payment_plan", "payment_method", "created_at",
            )}),
        ))

    return {
        "id": booking["id"],
        "sms_sent": booking["sms_sent"],
        "eta": eta_dict,
        "quote": quote_data,
        "grand_total": grand_total,
        "due_now": due_now,
        "due_later": due_later,
        "message": "Booking received! We'll be in touch shortly.",
    }


@api_router.get("/bookings/me")
async def my_bookings(user: dict = Depends(get_current_user)):
    docs = await db.bookings.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api_router.get("/bookings/upcoming")
async def upcoming_bookings(user: dict = Depends(get_current_user)):
    """Bookings with preferred_date >= today AND status != cancelled."""
    today = datetime.now(timezone.utc).date().isoformat()
    docs = await db.bookings.find(
        {"user_id": user["id"], "status": {"$ne": "cancelled"}, "preferred_date": {"$gte": today}},
        {"_id": 0},
    ).sort("preferred_date", 1).to_list(200)
    return docs


@api_router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id, "user_id": user["id"]})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.get("status") == "cancelled":
        return {"ok": True, "status": "cancelled"}
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}},
    )
    asyncio.create_task(fb.patch(f"bookings/{booking_id}", {"status": "cancelled"}))
    asyncio.create_task(fb.patch(f"user_bookings/{user['id']}/{booking_id}", {"status": "cancelled"}))
    return {"ok": True, "status": "cancelled"}


@api_router.get("/tos")
async def get_tos():
    return {"version": TOS_VERSION, "effective": TOS_EFFECTIVE, "text": TOS_TEXT}


@api_router.get("/firebase/status")
async def firebase_status():
    return {"enabled": fb.enabled(), "db_url": fb.FIREBASE_DB_URL if fb.enabled() else None}


@api_router.get("/bookings/recent")
async def recent_bookings(limit: int = 20):
    docs = await db.bookings.find({}, {"_id": 0, "tos_accepted": 0}).sort("created_at", -1).to_list(limit)
    return docs


# ============= Availability =============
@api_router.get("/availability")
async def availability(date: str, service: Optional[str] = None, tier: Optional[str] = None):
    """Return list of all time slots with `taken` and `too_late` flags for the given date.
    `service`+`tier` (optional) are used to compute slots that would push past closing time."""
    if not date:
        raise HTTPException(status_code=400, detail="date is required (YYYY-MM-DD)")
    slots = generate_time_slots()
    blocked = await get_blocked_minutes_for_date(date)
    duration_min = get_service_duration(service, tier) if service else 30
    _wmin_start, wmin_end = window_minutes()
    out = []
    for s in slots:
        smin = hhmm_to_minutes(s)
        taken = slot_conflicts(smin, duration_min, blocked)
        too_late = (smin + duration_min) > (wmin_end + 30)
        out.append({"time": s, "taken": taken, "too_late": too_late})
    return {
        "date": date,
        "min_time": BOOKING_TIME_MIN,
        "max_time": BOOKING_TIME_MAX,
        "duration_minutes": duration_min,
        "slots": out,
    }


# ============= PayPal (Orders v2 — on-site card processing) =============
class PayPalCreatePayload(BaseModel):
    amount: float
    currency: str = "USD"
    booking_ref: Optional[str] = None
    description: Optional[str] = None


class PayPalCapturePayload(BaseModel):
    order_id: str


@api_router.get("/paypal/config")
async def paypal_config():
    """Public PayPal config consumed by the frontend SDK loader."""
    return {
        "enabled": pp.enabled(),
        "env": pp.PAYPAL_ENV,
        "client_id": pp.PAYPAL_CLIENT_ID if pp.enabled() else None,
        "currency": "USD",
    }


@api_router.post("/paypal/create-order")
async def paypal_create(payload: PayPalCreatePayload):
    if not pp.enabled():
        raise HTTPException(status_code=503, detail="PayPal is not configured.")
    if payload.amount is None or payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0.")
    try:
        result = await pp.create_order(
            amount=payload.amount,
            currency=payload.currency or "USD",
            booking_ref=payload.booking_ref,
            description=payload.description or "Pawfect & Pristine booking",
        )
    except Exception as e:
        logger.warning(f"PayPal create_order error: {e}")
        raise HTTPException(status_code=502, detail=f"PayPal could not create the order. {str(e)[:140]}")
    return {"id": result.get("id"), "status": result.get("status"), "links": result.get("links", [])}


@api_router.post("/paypal/capture-order")
async def paypal_capture(payload: PayPalCapturePayload):
    if not pp.enabled():
        raise HTTPException(status_code=503, detail="PayPal is not configured.")
    try:
        result = await pp.capture_order(payload.order_id)
    except Exception as e:
        logger.warning(f"PayPal capture_order error: {e}")
        raise HTTPException(status_code=502, detail=f"PayPal capture failed. {str(e)[:140]}")
    # Walk the response for the actual capture id + amount
    capture_id = None
    captured_amount = None
    try:
        pu = (result.get("purchase_units") or [{}])[0]
        cap = ((pu.get("payments") or {}).get("captures") or [{}])[0]
        capture_id = cap.get("id")
        amt = cap.get("amount") or {}
        captured_amount = float(amt.get("value")) if amt.get("value") else None
    except Exception:
        pass
    return {
        "id": result.get("id"),
        "status": result.get("status"),
        "capture_id": capture_id,
        "captured_amount": captured_amount,
        "raw": {"status": result.get("status"), "payer": result.get("payer", {}).get("email_address")},
    }


# ============= Admin =============
async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def _safe_booking(d: dict) -> dict:
    d = {k: v for k, v in d.items() if k != "_id" and k != "tos_accepted"}
    return d


@api_router.get("/admin/bookings/today")
async def admin_today(_admin: dict = Depends(require_admin)):
    today = datetime.now(timezone.utc).date().isoformat()
    docs = await db.bookings.find(
        {"preferred_date": today, "status": {"$ne": "cancelled"}},
        {"_id": 0, "tos_accepted": 0},
    ).sort("preferred_time", 1).to_list(500)
    return docs


@api_router.get("/admin/bookings/upcoming")
async def admin_upcoming(_admin: dict = Depends(require_admin)):
    today = datetime.now(timezone.utc).date().isoformat()
    docs = await db.bookings.find(
        {"preferred_date": {"$gte": today}, "status": {"$nin": ["cancelled", "completed"]}},
        {"_id": 0, "tos_accepted": 0},
    ).sort([("preferred_date", 1), ("preferred_time", 1)]).to_list(500)
    return docs


@api_router.get("/admin/bookings/all")
async def admin_all(limit: int = 200, _admin: dict = Depends(require_admin)):
    docs = await db.bookings.find({}, {"_id": 0, "tos_accepted": 0}).sort("created_at", -1).to_list(limit)
    return docs


@api_router.get("/admin/stats")
async def admin_stats(_admin: dict = Depends(require_admin)):
    today = datetime.now(timezone.utc).date().isoformat()
    today_docs = await db.bookings.find(
        {"preferred_date": today, "status": {"$ne": "cancelled"}}, {"_id": 0, "grand_total": 1}
    ).to_list(500)
    today_revenue = round(sum((d.get("grand_total", 0) or 0) for d in today_docs), 2)
    upcoming_count = await db.bookings.count_documents(
        {"preferred_date": {"$gte": today}, "status": {"$nin": ["cancelled", "completed"]}}
    )
    customers_count = await db.users.count_documents({"role": {"$ne": "admin"}})
    return {
        "today_bookings": len(today_docs),
        "today_revenue": today_revenue,
        "upcoming_count": upcoming_count,
        "customers_count": customers_count,
    }


@api_router.post("/admin/bookings/{booking_id}/notify-otw")
async def admin_notify_otw(booking_id: str, _admin: dict = Depends(require_admin)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    now = datetime.now(timezone.utc).isoformat()
    sms_body = (
        f"Hi {booking.get('name', 'there')}! This is Pawfect & Pristine — "
        f"I'm on the way to your {booking.get('service_label', 'service')} now. See you soon! 🐾"
    )
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "on_the_way", "otw_notified_at": now}},
    )
    asyncio.create_task(fb.patch(f"bookings/{booking_id}", {"status": "on_the_way", "otw_notified_at": now}))
    # Return tel:/sms: deeplinks — admin's device will open native Messages
    return {"ok": True, "sms_sent": False, "sms_body": sms_body,
            "tel_link": f"tel:{booking.get('phone')}",
            "sms_link": f"sms:{booking.get('phone')}?&body={quote_plus(sms_body)}"}


@api_router.post("/admin/bookings/{booking_id}/status")
async def admin_set_status(booking_id: str, body: StatusBody, _admin: dict = Depends(require_admin)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": body.status, "status_updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    asyncio.create_task(fb.patch(f"bookings/{booking_id}", {"status": body.status}))
    return {"ok": True, "status": body.status}


@api_router.post("/admin/bookings/{booking_id}/reschedule")
async def admin_reschedule(booking_id: str, body: RescheduleBody, _admin: dict = Depends(require_admin)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if not is_time_in_window(body.preferred_time):
        raise HTTPException(status_code=400, detail=f"Time must be between {BOOKING_TIME_MIN} and {BOOKING_TIME_MAX}.")
    duration_min = booking.get("duration_minutes") or get_service_duration(
        booking.get("service_value"), booking.get("tier_key")
    )
    try:
        start_min = hhmm_to_minutes(body.preferred_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid time.")
    _wmin_start, wmin_end = window_minutes()
    if start_min + duration_min > wmin_end + 30:
        raise HTTPException(status_code=400, detail=f"Service ({duration_min} min) runs past close ({BOOKING_TIME_MAX}).")
    blocked = await get_blocked_minutes_for_date(body.preferred_date, exclude_booking_id=booking_id)
    if slot_conflicts(start_min, duration_min, blocked):
        raise HTTPException(status_code=409, detail="That time slot overlaps another booking.")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "preferred_date": body.preferred_date,
            "preferred_time": body.preferred_time,
            "rescheduled_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    asyncio.create_task(fb.patch(f"bookings/{booking_id}", {
        "preferred_date": body.preferred_date,
        "preferred_time": body.preferred_time,
    }))
    return {"ok": True, "preferred_date": body.preferred_date, "preferred_time": body.preferred_time}


@api_router.post("/admin/bookings/{booking_id}/cancel")
async def admin_cancel(booking_id: str, _admin: dict = Depends(require_admin)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": "admin",
        }},
    )
    asyncio.create_task(fb.patch(f"bookings/{booking_id}", {"status": "cancelled"}))
    return {"ok": True, "status": "cancelled"}


@api_router.get("/admin/customers")
async def admin_customers(_admin: dict = Depends(require_admin)):
    docs = await db.users.find(
        {"role": {"$ne": "admin"}},
        {"_id": 0, "password_hash": 0},
    ).sort("created_at", -1).to_list(500)
    # Attach booking count
    for d in docs:
        d["booking_count"] = await db.bookings.count_documents({"user_id": d["id"]})
    return docs


# ============= App setup =============
app.include_router(api_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.bookings.create_index("user_id")
    await db.bookings.create_index("created_at")
    await db.login_attempts.create_index("identifier", unique=True)

    # Seed admin
    if ADMIN_EMAIL and ADMIN_PASSWORD:
        existing = await db.users.find_one({"email": ADMIN_EMAIL.lower()})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "name": "Admin",
                "email": ADMIN_EMAIL.lower(),
                "password_hash": hash_password(ADMIN_PASSWORD),
                "role": "admin",
                "phone": None,
                "created_at": datetime.now(timezone.utc),
            })
            logger.info("Seeded admin user")
        elif not verify_password(ADMIN_PASSWORD, existing.get("password_hash", "")):
            await db.users.update_one(
                {"email": ADMIN_EMAIL.lower()},
                {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}},
            )
            logger.info("Updated admin password")


@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()

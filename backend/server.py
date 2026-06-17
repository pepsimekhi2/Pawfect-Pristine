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
from twilio.rest import Client as TwilioClient

from auth_utils import (
    hash_password, verify_password, create_access_token, decode_token, extract_token
)
from pricing import compute_quote, get_public_catalog, SERVICE_CATALOG, generate_time_slots, is_time_in_window, BOOKING_TIME_MIN, BOOKING_TIME_MAX, get_service_duration, hhmm_to_minutes, window_minutes
from tos import TOS_TEXT, TOS_VERSION, TOS_EFFECTIVE
import firebase_sync as fb
import asyncio

mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ['DB_NAME']]

TWILIO_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM = os.environ.get('TWILIO_FROM_NUMBER')
OWNER_PHONE = os.environ.get('OWNER_PHONE')
ORIGIN_LAT = float(os.environ.get('ORIGIN_LAT', '33.7748'))
ORIGIN_LON = float(os.environ.get('ORIGIN_LON', '-84.2963'))
ORIGIN_LABEL = os.environ.get('ORIGIN_LABEL', 'Decatur, GA')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
ADMIN_PASSPHRASE = os.environ.get('ADMIN_PASSPHRASE', 'duck')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
RESEND_FROM = os.environ.get('RESEND_FROM', 'Pawfect & Pristine <onboarding@resend.dev>')
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
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": "us"}
    headers = {"User-Agent": "PawfectPristine/1.0 (booking@pawfectpristine.local)"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "display_name": data[0]["display_name"]}


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
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and OWNER_PHONE):
        return False
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=body, from_=TWILIO_FROM, to=OWNER_PHONE)
        return True
    except Exception as e:
        logger.error(f"Twilio failed: {e}")
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
    <div style="font-family:Arial,sans-serif;line-height:1.6;color:#1f2a24">
      <h2>Welcome, {safe_name}.</h2>
      <p>Thanks for joining Pawfect &amp; Pristine. Your first logged-in booking gets 25% off automatically.</p>
      <p>Book whenever you are ready, and the discount will show in your running total before checkout.</p>
      <p style="font-size:12px;color:#5f6f67">You can unsubscribe from promotional emails at any time.</p>
    </div>
    """


async def send_resend_email(to_email: str, subject: str, html_body: str) -> bool:
    if not RESEND_API_KEY:
        return False
    payload = {
        "from": RESEND_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            )
        if response.status_code >= 400:
            logger.warning(f"Resend email failed for {to_email}: {response.status_code} {response.text[:120]}")
            return False
        return True
    except Exception as e:
        logger.warning(f"Resend email failed for {to_email}: {e}")
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


# ============= Booking Routes =============
@api_router.post("/bookings")
async def create_booking(payload: BookingCreate, request: Request):
    user = await maybe_current_user(request)

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

    # Compute ETA if possible
    eta_dict = None
    try:
        geo = await geocode_nominatim(payload.address)
        if geo:
            route = await osrm_route(ORIGIN_LAT, ORIGIN_LON, geo["lat"], geo["lon"])
            if route:
                miles = round(route["distance_meters"] / 1609.34, 2)
                mins = round(route["duration_seconds"] / 60, 1)
                z = classify_zone(miles)
                eta_dict = {"distance_miles": miles, "duration_minutes": mins,
                            "zone": z["zone"], "extra_fee": z["extra_fee"]}
    except Exception:
        pass

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

    booking = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"] if user else None,
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
        "payment_status": (
            "paid_full_pending_verify" if payload.payment_plan == "all_now" and payload.payment_method == "paypal"
            else "paid_half_pending_verify" if payload.payment_plan == "half_now" and payload.payment_method == "paypal"
            else "unpaid"
        ),
        "status": "scheduled",
        "eta": eta_dict,
        "tos_accepted": True,
        "tos_accepted_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    booking["sms_sent"] = False

    # Build SMS body
    eta_line = ""
    if eta_dict:
        eta_line = f" · {eta_dict['distance_miles']}mi/~{int(eta_dict['duration_minutes'])}min"
        if eta_dict["extra_fee"] > 0:
            eta_line += f" (+${eta_dict['extra_fee']} travel)"
    when = f"{payload.preferred_date} {payload.preferred_time}".strip() or "ASAP"
    pay_summary = {
        "all_now": "PAID IN FULL via PayPal (verify)" if payload.payment_method == "paypal" else "PAID IN FULL",
        "half_now": f"HALF PAID via PayPal (${due_now}, verify) · ${due_later} on arrival" if payload.payment_method == "paypal"
                     else f"HALF PAID (${due_now}) · ${due_later} on arrival",
        "pay_later": f"PAY ON ARRIVAL · ${grand_total} {payload.payment_method}",
    }[payload.payment_plan]

    sms_body = (
        f"🐾 New Pawfect booking!\n"
        f"{payload.name} ({payload.phone})\n"
        f"{quote_data['service_label']}"
        + (f" — {quote_data['tier_label']}" if quote_data["tier_label"] else "") + "\n"
        f"When: {when}\n"
        f"Addr: {payload.address}{eta_line}\n"
        f"${grand_total} · {pay_summary}"
    )
    if payload.notes:
        sms_body += f"\nNote: {payload.notes[:100]}"

    booking["sms_sent"] = send_owner_sms(sms_body)

    await db.bookings.insert_one(booking)

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
    sms_sent = False
    if TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and booking.get("phone"):
        try:
            client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
            client.messages.create(body=sms_body, from_=TWILIO_FROM, to=booking["phone"])
            sms_sent = True
        except Exception as e:
            logger.warning(f"Twilio send failed: {e}")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "on_the_way", "otw_notified_at": now, "otw_sms_sent": sms_sent}},
    )
    asyncio.create_task(fb.patch(f"bookings/{booking_id}", {"status": "on_the_way", "otw_notified_at": now}))
    return {"ok": True, "sms_sent": sms_sent, "sms_body": sms_body if not sms_sent else None,
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

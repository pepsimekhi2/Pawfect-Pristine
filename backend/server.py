from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone, timedelta
from twilio.rest import Client as TwilioClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ---------- Models ----------
class ETARequest(BaseModel):
    address: str


class ETAResponse(BaseModel):
    address: str
    resolved_address: str
    distance_miles: float
    duration_minutes: float
    arrival_time: str  # HH:MM AM/PM
    arrival_window: str
    zone: Literal["standard", "extended", "out_of_range"]
    extra_fee: int
    zone_label: str
    zone_message: str


class BookingCreate(BaseModel):
    name: str
    phone: str
    address: str
    service_category: Literal["home", "pet"]
    service_type: str
    pets: int = 0
    bedrooms: int = 0
    bathrooms: int = 0
    notes: str = ""
    preferred_date: str = ""
    preferred_time: str = ""


class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    address: str
    service_category: str
    service_type: str
    pets: int
    bedrooms: int
    bathrooms: int
    notes: str
    preferred_date: str
    preferred_time: str
    eta: Optional[dict] = None
    sms_sent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Helpers ----------
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
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"],
        }


async def osrm_route(o_lat: float, o_lon: float, d_lat: float, d_lon: float) -> Optional[dict]:
    url = f"https://router.project-osrm.org/route/v1/driving/{o_lon},{o_lat};{d_lon},{d_lat}"
    params = {"overview": "false"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        route = data["routes"][0]
        return {
            "distance_meters": route["distance"],
            "duration_seconds": route["duration"],
        }


def classify_zone(miles: float) -> dict:
    if miles <= 7:
        return {
            "zone": "standard",
            "extra_fee": 0,
            "zone_label": "Standard Service Area",
            "zone_message": "You're right in our happy zone — no extra fees!",
        }
    if miles <= 13:
        return {
            "zone": "extended",
            "extra_fee": 20,
            "zone_label": "Extended Service Area",
            "zone_message": "We can swing by — a small $20 travel fee applies.",
        }
    return {
        "zone": "out_of_range",
        "extra_fee": 0,
        "zone_label": "Out of Range",
        "zone_message": "You're a bit far for our regular routes. Call us at (470) 381-4682 for a custom quote!",
    }


def format_arrival(duration_minutes: float) -> tuple[str, str]:
    now = datetime.now(timezone.utc) - timedelta(hours=5)  # roughly ET; display-only
    arrival = now + timedelta(minutes=duration_minutes + 15)  # +15 min buffer to pack up
    window_end = arrival + timedelta(minutes=20)

    def fmt(dt: datetime) -> str:
        h = dt.hour % 12
        h = 12 if h == 0 else h
        suffix = "AM" if dt.hour < 12 else "PM"
        return f"{h}:{dt.minute:02d} {suffix}"

    return fmt(arrival), f"{fmt(arrival)} – {fmt(window_end)}"


def send_owner_sms(body: str) -> bool:
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and OWNER_PHONE):
        logger.warning("Twilio not fully configured; skipping SMS")
        return False
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(body=body, from_=TWILIO_FROM, to=OWNER_PHONE)
        logger.info(f"SMS sent: SID={msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Twilio send failed: {e}")
        return False


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Pawfect & Pristine API ready"}


@api_router.post("/eta", response_model=ETAResponse)
async def calculate_eta(payload: ETARequest):
    address = payload.address.strip()
    if not address:
        raise HTTPException(status_code=400, detail="Address required")

    geo = await geocode_nominatim(address)
    if not geo:
        raise HTTPException(status_code=404, detail="We couldn't find that address. Try including city + state.")

    route = await osrm_route(ORIGIN_LAT, ORIGIN_LON, geo["lat"], geo["lon"])
    if not route:
        raise HTTPException(status_code=502, detail="Routing service unavailable. Try again.")

    distance_miles = round(route["distance_meters"] / 1609.34, 2)
    duration_minutes = round(route["duration_seconds"] / 60, 1)
    zone_info = classify_zone(distance_miles)
    arrival_time, window = format_arrival(duration_minutes)

    return ETAResponse(
        address=address,
        resolved_address=geo["display_name"],
        distance_miles=distance_miles,
        duration_minutes=duration_minutes,
        arrival_time=arrival_time,
        arrival_window=window,
        **zone_info,
    )


@api_router.post("/bookings")
async def create_booking(payload: BookingCreate):
    booking = Booking(**payload.model_dump())

    # Try ETA if address looks usable
    eta_dict = None
    try:
        geo = await geocode_nominatim(payload.address)
        if geo:
            route = await osrm_route(ORIGIN_LAT, ORIGIN_LON, geo["lat"], geo["lon"])
            if route:
                miles = round(route["distance_meters"] / 1609.34, 2)
                mins = round(route["duration_seconds"] / 60, 1)
                zone_info = classify_zone(miles)
                eta_dict = {
                    "distance_miles": miles,
                    "duration_minutes": mins,
                    "zone": zone_info["zone"],
                    "extra_fee": zone_info["extra_fee"],
                }
    except Exception as e:
        logger.warning(f"ETA in booking failed: {e}")

    booking.eta = eta_dict

    # Build SMS body for owner
    eta_line = ""
    if eta_dict:
        eta_line = f" • {eta_dict['distance_miles']}mi / ~{int(eta_dict['duration_minutes'])}min"
        if eta_dict["extra_fee"] > 0:
            eta_line += f" (+${eta_dict['extra_fee']} travel)"
    detail_bits = []
    if payload.pets:
        detail_bits.append(f"{payload.pets} pet(s)")
    if payload.bedrooms:
        detail_bits.append(f"{payload.bedrooms} BR")
    if payload.bathrooms:
        detail_bits.append(f"{payload.bathrooms} BA")
    detail_str = " · ".join(detail_bits) if detail_bits else ""

    when = f"{payload.preferred_date} {payload.preferred_time}".strip() or "ASAP"

    sms_body = (
        f"🐾 New Pawfect booking!\n"
        f"{payload.name} ({payload.phone})\n"
        f"{payload.service_type} [{payload.service_category}]\n"
        f"When: {when}\n"
        f"Addr: {payload.address}{eta_line}"
    )
    if detail_str:
        sms_body += f"\n{detail_str}"
    if payload.notes:
        sms_body += f"\nNote: {payload.notes[:100]}"

    booking.sms_sent = send_owner_sms(sms_body)

    doc = booking.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.bookings.insert_one(doc)

    return {
        "id": booking.id,
        "sms_sent": booking.sms_sent,
        "eta": eta_dict,
        "message": "Booking received! We'll be in touch shortly.",
    }


@api_router.get("/bookings/recent")
async def recent_bookings(limit: int = 20):
    docs = await db.bookings.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return docs


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()

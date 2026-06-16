"""Pricing catalog and computation logic."""
from typing import Optional
from datetime import datetime, timezone

# All prices in USD. "tiers" is dict of {tier_key: {"label": str, "price": int, "desc": str}}.
# v1.2 — prices significantly reduced per owner's directive (2026-06-16).
SERVICE_CATALOG = {
    "general_cleaning": {
        "label": "General Cleaning",
        "category": "home",
        "icon": "🧹",
        "has_tiers": True,
        "tier_question": "How messy is the space?",
        "tiers": {
            "light": {"label": "Lightly lived-in", "price": 15, "desc": "Quick refresh; surfaces tidy already."},
            "standard": {"label": "Standard", "price": 55, "desc": "Normal weekly mess."},
            "heavy": {"label": "Heavy", "price": 115, "desc": "A few weeks of build-up."},
            "disaster": {"label": "Disaster zone", "price": 250, "desc": "Bring backup — we love a challenge."},
        },
    },
    "deep_cleaning": {
        "label": "Deep Cleaning",
        "category": "home",
        "icon": "✨",
        "has_tiers": True,
        "tier_question": "How big is the space?",
        "tiers": {
            "studio": {"label": "Studio / 1 BR", "price": 80, "desc": "Top-to-bottom reset."},
            "small": {"label": "2 BR home", "price": 130, "desc": "Full deep clean inside & out."},
            "medium": {"label": "3 BR home", "price": 190, "desc": "Behind appliances, cabinets, grout."},
            "large": {"label": "4+ BR home", "price": 260, "desc": "The whole house, every inch."},
        },
    },
    "organizing": {
        "label": "Organizing",
        "category": "home",
        "icon": "📦",
        "has_tiers": True,
        "tier_question": "How much chaos are we taming?",
        "tiers": {
            "drawer": {"label": "A drawer or closet", "price": 25, "desc": "Focused 2-hour reset."},
            "room": {"label": "A whole room", "price": 65, "desc": "Sort, donate, label."},
            "house": {"label": "Multiple rooms", "price": 140, "desc": "Half-day with full systems."},
        },
    },
    "garage_shed": {
        "label": "Garages & Sheds",
        "category": "home",
        "icon": "🏠",
        "has_tiers": True,
        "tier_question": "What are we dealing with?",
        "tiers": {
            "tidy": {"label": "Mildly cluttered", "price": 60, "desc": "Sort, sweep, organize."},
            "busy": {"label": "Years of stuff", "price": 130, "desc": "Heavy lift, dump runs included up to 1."},
            "full": {"label": "Can't see the floor", "price": 240, "desc": "Bring the team. We'll fix it."},
        },
    },
    "dog_walking": {
        "label": "Dog Walking",
        "category": "pet",
        "icon": "🐕",
        "has_tiers": True,
        "tier_question": "Walk length?",
        "tiers": {
            "30": {"label": "30 min", "price": 12, "desc": "Quick neighborhood loop."},
            "60": {"label": "60 min", "price": 20, "desc": "Real exercise; energy burned."},
            "90": {"label": "90 min", "price": 30, "desc": "Long adventure walk."},
        },
    },
    "pet_sitting": {
        "label": "Pet Sitting",
        "category": "pet",
        "icon": "🐱",
        "has_tiers": True,
        "tier_question": "What kind of stay?",
        "tiers": {
            "dropin": {"label": "Drop-in (30 min)", "price": 12, "desc": "Feed, water, snuggle."},
            "halfday": {"label": "Half day", "price": 30, "desc": "Up to 4 hours of company."},
            "overnight": {"label": "Overnight (12 hr)", "price": 55, "desc": "We stay over so they don't feel alone."},
        },
    },
    "feeding_care": {
        "label": "Feeding & Care",
        "category": "pet",
        "icon": "🍽️",
        "has_tiers": True,
        "tier_question": "How many visits?",
        "tiers": {
            "1": {"label": "1 visit", "price": 10, "desc": "Single drop-in for meals/meds."},
            "2": {"label": "2 visits / day", "price": 18, "desc": "Morning + evening."},
            "3": {"label": "3 visits / day", "price": 28, "desc": "Full day coverage."},
        },
    },
    "playtime": {
        "label": "Playtime & Enrichment",
        "category": "pet",
        "icon": "🎾",
        "has_tiers": True,
        "tier_question": "How much enrichment?",
        "tiers": {
            "30": {"label": "30 min play", "price": 12, "desc": "Fetch, tug, sniff."},
            "60": {"label": "60 min play", "price": 20, "desc": "Mental + physical workout."},
            "puzzle": {"label": "60 min + puzzle work", "price": 30, "desc": "Enrichment toys + bonding."},
        },
    },
}

ADVANCE_FEE_USD = 0.99
ADVANCE_FEE_DAYS = 7

# Booking time window (24h local time, military). Earliest start, latest start.
BOOKING_TIME_MIN = "09:00"
BOOKING_TIME_MAX = "18:30"


def compute_quote(service_value: str, tier_key: Optional[str], preferred_date_iso: Optional[str]) -> dict:
    """Compute the total price quote for a booking."""
    svc = SERVICE_CATALOG.get(service_value)
    if not svc:
        return {
            "base_price": 0,
            "advance_fee": 0,
            "total": 0,
            "currency": "USD",
            "breakdown": [],
            "service_label": service_value,
            "tier_label": None,
            "is_advance": False,
        }

    if svc["has_tiers"]:
        tier = svc["tiers"].get(tier_key) if tier_key else None
        if not tier:
            tier_key, tier = next(iter(svc["tiers"].items()))
        base = tier["price"]
        tier_label = tier["label"]
    else:
        base = 0
        tier_label = None

    advance_fee = 0.0
    is_advance = False
    if preferred_date_iso:
        try:
            d = datetime.fromisoformat(preferred_date_iso.replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            delta_days = (d - datetime.now(timezone.utc)).total_seconds() / 86400
            if delta_days >= ADVANCE_FEE_DAYS:
                advance_fee = ADVANCE_FEE_USD
                is_advance = True
        except Exception:
            pass

    total = round(base + advance_fee, 2)
    breakdown = [{"label": f"{svc['label']} — {tier_label}" if tier_label else svc["label"], "amount": base}]
    if advance_fee > 0:
        breakdown.append({"label": f"Advance booking fee (≥{ADVANCE_FEE_DAYS} days out)", "amount": advance_fee})

    return {
        "base_price": base,
        "advance_fee": advance_fee,
        "total": total,
        "currency": "USD",
        "breakdown": breakdown,
        "service_label": svc["label"],
        "tier_label": tier_label,
        "is_advance": is_advance,
    }


def get_public_catalog() -> dict:
    out = {}
    for key, svc in SERVICE_CATALOG.items():
        out[key] = {
            "label": svc["label"],
            "category": svc["category"],
            "icon": svc["icon"],
            "has_tiers": svc["has_tiers"],
            "tier_question": svc.get("tier_question"),
            "tiers": [
                {"key": tk, **tv} for tk, tv in svc.get("tiers", {}).items()
            ],
        }
    return out


def generate_time_slots(step_minutes: int = 30) -> list:
    """Return list of HH:MM strings between BOOKING_TIME_MIN and BOOKING_TIME_MAX inclusive."""
    out = []
    sh, sm = map(int, BOOKING_TIME_MIN.split(":"))
    eh, em = map(int, BOOKING_TIME_MAX.split(":"))
    start = sh * 60 + sm
    end = eh * 60 + em
    t = start
    while t <= end:
        h, m = divmod(t, 60)
        out.append(f"{h:02d}:{m:02d}")
        t += step_minutes
    return out


def is_time_in_window(hhmm: str) -> bool:
    try:
        h, m = map(int, hhmm.split(":"))
        sh, sm = map(int, BOOKING_TIME_MIN.split(":"))
        eh, em = map(int, BOOKING_TIME_MAX.split(":"))
        return (sh * 60 + sm) <= (h * 60 + m) <= (eh * 60 + em)
    except Exception:
        return False

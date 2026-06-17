"""Pricing catalog and computation logic."""
from typing import Optional
from datetime import datetime, timezone

# All prices in USD. "tiers" is dict of {tier_key: {"label": str, "price": int, "desc": str, "duration": minutes}}.
# `duration` = minutes the service occupies on the calendar; used for auto-blocking overlapping slots.
# v1.3 — added service durations for calendar blocking (2026-02-14).
SERVICE_CATALOG = {
    "general_cleaning": {
        "label": "General Cleaning",
        "category": "home",
        "icon": "🧹",
        "has_tiers": True,
        "tier_question": "How messy is the space?",
        "tiers": {
            "light":    {"label": "Lightly lived-in", "price": 15,  "duration": 60,  "desc": "Quick refresh; surfaces tidy already."},
            "standard": {"label": "Standard",         "price": 55,  "duration": 120, "desc": "Normal weekly mess."},
            "heavy":    {"label": "Heavy",            "price": 115, "duration": 180, "desc": "A few weeks of build-up."},
            "disaster": {"label": "Disaster zone",    "price": 250, "duration": 240, "desc": "Bring backup — we love a challenge."},
        },
    },
    "deep_cleaning": {
        "label": "Deep Cleaning",
        "category": "home",
        "icon": "✨",
        "has_tiers": True,
        "tier_question": "How big is the space?",
        "tiers": {
            "studio": {"label": "Studio / 1 BR", "price": 80,  "duration": 120, "desc": "Top-to-bottom reset."},
            "small":  {"label": "2 BR home",     "price": 130, "duration": 180, "desc": "Full deep clean inside & out."},
            "medium": {"label": "3 BR home",     "price": 190, "duration": 240, "desc": "Behind appliances, cabinets, grout."},
            "large":  {"label": "4+ BR home",    "price": 260, "duration": 360, "desc": "The whole house, every inch."},
        },
    },
    "organizing": {
        "label": "Organizing",
        "category": "home",
        "icon": "📦",
        "has_tiers": True,
        "tier_question": "How much chaos are we taming?",
        "tiers": {
            "drawer": {"label": "A drawer or closet", "price": 25,  "duration": 60,  "desc": "Focused 2-hour reset."},
            "room":   {"label": "A whole room",       "price": 65,  "duration": 120, "desc": "Sort, donate, label."},
            "house":  {"label": "Multiple rooms",     "price": 140, "duration": 240, "desc": "Half-day with full systems."},
        },
    },
    "garage_shed": {
        "label": "Garages & Sheds",
        "category": "home",
        "icon": "🏠",
        "has_tiers": True,
        "tier_question": "What are we dealing with?",
        "tiers": {
            "tidy": {"label": "Mildly cluttered",   "price": 60,  "duration": 120, "desc": "Sort, sweep, organize."},
            "busy": {"label": "Years of stuff",     "price": 130, "duration": 240, "desc": "Heavy lift, dump runs included up to 1."},
            "full": {"label": "Can't see the floor", "price": 240, "duration": 360, "desc": "Bring the team. We'll fix it."},
        },
    },
    "dog_walking": {
        "label": "Dog Walking",
        "category": "pet",
        "icon": "🐕",
        "has_tiers": True,
        "tier_question": "Walk length?",
        "tiers": {
            "30": {"label": "30 min", "price": 12, "duration": 30, "desc": "Quick neighborhood loop."},
            "60": {"label": "60 min", "price": 20, "duration": 60, "desc": "Real exercise; energy burned."},
            "90": {"label": "90 min", "price": 30, "duration": 90, "desc": "Long adventure walk."},
        },
    },
    "pet_sitting": {
        "label": "Pet Sitting",
        "category": "pet",
        "icon": "🐱",
        "has_tiers": True,
        "tier_question": "What kind of stay?",
        "tiers": {
            "dropin":  {"label": "Drop-in (30 min)", "price": 12, "duration": 30,  "desc": "Feed, water, snuggle."},
            "halfday": {"label": "Half day",         "price": 30, "duration": 240, "desc": "Up to 4 hours of company."},
        },
    },
    "playtime": {
        "label": "Playtime & Enrichment",
        "category": "pet",
        "icon": "🎾",
        "has_tiers": True,
        "tier_question": "How much enrichment?",
        "tiers": {
            "30":     {"label": "30 min play",          "price": 12, "duration": 30, "desc": "Fetch, tug, sniff."},
            "60":     {"label": "60 min play",          "price": 20, "duration": 60, "desc": "Mental + physical workout."},
            "puzzle": {"label": "60 min + puzzle work", "price": 30, "duration": 60, "desc": "Enrichment toys + bonding."},
        },
    },
}

ADVANCE_FEE_USD = 0.99
ADVANCE_FEE_DAYS = 7
FIRST_TIME_DISCOUNT_PCT = 0.25

# Booking time window (24h local time, military). Earliest start, latest start.
BOOKING_TIME_MIN = "09:00"
BOOKING_TIME_MAX = "18:30"

# ─────────────────────────────────────────────────────────────────────
# Upsell catalogue — extra questionnaire items / add-ons / discounts.
# ─────────────────────────────────────────────────────────────────────

# Add-ons grouped by which service category they apply to.
CLEANING_ADDONS = [
    {"key": "baseboards",  "label": "Baseboard detailing",   "price": 15, "icon": "📐", "desc": "Hand-wiped, dust-free."},
    {"key": "int_windows", "label": "Window cleaning",       "price": 20, "icon": "🪟", "desc": "Streak-free shine, sills wiped."},
    {"key": "dishes",      "label": "Dishwashing",           "price": 12, "icon": "🍽️", "desc": "We'll knock 'em out."},
    {"key": "laundry",     "label": "Laundry (per load)",    "price": 10, "icon": "🧺", "desc": "Wash, dry, fold."},
    {"key": "move_in_out", "label": "Move in / Move out",    "price": 50, "icon": "📦", "desc": "Floor-to-ceiling, every closet."},
]

PET_ADDONS = [
    {"key": "photos", "label": "Photo updates",   "price": 3, "icon": "📸", "desc": "We text 3-5 cute pics during the visit."},
    {"key": "plants", "label": "Water the plants","price": 5, "icon": "🪴", "desc": "Indoor or outdoor — you provide the watering can."},
    {"key": "mail",   "label": "Bring in mail",   "price": 5, "icon": "📬", "desc": "Mail & packages stacked inside the door."},
]

# Property type options — only shown for cleaning category services.
PROPERTY_TYPES = [
    {"key": "house",     "label": "House",              "modifier": 0.0,  "badge": None,    "icon": "🏠"},
    {"key": "apartment", "label": "Apartment / Condo",  "modifier": 0.0,  "badge": None,    "icon": "🏢"},
    {"key": "business",  "label": "Business / Commercial","modifier": 0.30, "badge": "+30%", "icon": "🏪"},
]

# Per-unit upsells for cleaning (asks # bedrooms / bathrooms)
ROOM_QUESTIONS = {
    "bedrooms":  {"label": "Bedrooms",  "min": 0, "max": 10, "free_units": 2, "price_each": 15, "icon": "🛏️"},
    "bathrooms": {"label": "Bathrooms", "min": 1, "max": 8,  "free_units": 1, "price_each": 10, "icon": "🚿"},
}

# Per-unit upsells for pet services (asks # of pets)
PET_COUNT_QUESTION = {"label": "How many pets total?", "min": 1, "max": 8, "free_units": 1, "price_each": 5, "icon": "🐶"}

# Discounts — keyed
DISCOUNTS = {
    "byo_supplies": {
        "label": "I'll have supplies ready (bleach, gloves, cleaner, etc.)",
        "sublabel": "Out and ready when we arrive — we won't need to bring our own.",
        "pct": 0.15,
        "icon": "🧴",
        "applies_to_categories": ["home"],
    },
}


def _starts_at(svc: dict) -> Optional[int]:
    if not svc.get("has_tiers"):
        return svc.get("price")
    try:
        return min(t["price"] for t in svc["tiers"].values())
    except Exception:
        return None


def _service_upsell_meta(svc_value: str, svc: dict) -> dict:
    """Return the upsell question schema for a given service."""
    category = svc.get("category")
    meta = {"property_types": [], "room_questions": {}, "pet_question": None, "addons": [], "discounts": []}
    if category == "home":
        meta["property_types"] = PROPERTY_TYPES
        meta["room_questions"] = ROOM_QUESTIONS
        # Filter cleaning add-ons: deep-clean-only addons (move_in_out) only show on deep_cleaning
        meta["addons"] = [
            a for a in CLEANING_ADDONS
            if a["key"] != "move_in_out" or svc_value in ("deep_cleaning", "general_cleaning")
        ]
        meta["discounts"] = [{"key": k, **v} for k, v in DISCOUNTS.items() if "home" in v["applies_to_categories"]]
    elif category == "pet":
        meta["pet_question"] = PET_COUNT_QUESTION
        meta["addons"] = PET_ADDONS
    return meta


def compute_quote(
    service_value: str,
    tier_key: Optional[str],
    preferred_date_iso: Optional[str],
    *,
    property_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    pet_count: Optional[int] = None,
    addon_keys: Optional[list] = None,
    discount_keys: Optional[list] = None,
    first_time_customer: bool = False,
) -> dict:
    """Compute the total price quote, factoring in upsells & discounts."""
    svc = SERVICE_CATALOG.get(service_value)
    if not svc:
        return {
            "base_price": 0, "advance_fee": 0, "total": 0, "currency": "USD",
            "breakdown": [], "service_label": service_value, "tier_label": None, "is_advance": False,
        }

    if svc.get("has_tiers"):
        tier = svc["tiers"].get(tier_key) if tier_key else None
        if not tier:
            tier_key, tier = next(iter(svc["tiers"].items()))
        base = tier["price"]
        tier_label = tier["label"]
    else:
        base = 0
        tier_label = None

    breakdown = [{"label": f"{svc['label']} — {tier_label}" if tier_label else svc["label"], "amount": base}]
    pre_discount = float(base)

    # --- Room counts (cleaning only) ---
    if svc.get("category") == "home":
        if bedrooms is not None:
            cfg = ROOM_QUESTIONS["bedrooms"]
            extra = max(0, int(bedrooms) - cfg["free_units"])
            if extra > 0:
                amount = extra * cfg["price_each"]
                pre_discount += amount
                breakdown.append({"label": f"{extra} extra bedroom{'s' if extra>1 else ''}", "amount": amount})
        if bathrooms is not None:
            cfg = ROOM_QUESTIONS["bathrooms"]
            extra = max(0, int(bathrooms) - cfg["free_units"])
            if extra > 0:
                amount = extra * cfg["price_each"]
                pre_discount += amount
                breakdown.append({"label": f"{extra} extra bathroom{'s' if extra>1 else ''}", "amount": amount})

    # --- Pet count (pet services only) ---
    if svc.get("category") == "pet" and pet_count is not None:
        cfg = PET_COUNT_QUESTION
        extra = max(0, int(pet_count) - cfg["free_units"])
        if extra > 0:
            amount = extra * cfg["price_each"]
            pre_discount += amount
            breakdown.append({"label": f"{extra} extra pet{'s' if extra>1 else ''}", "amount": amount})

    # --- Add-ons ---
    addon_keys = addon_keys or []
    addon_pool = CLEANING_ADDONS if svc.get("category") == "home" else PET_ADDONS
    addon_lookup = {a["key"]: a for a in addon_pool}
    for k in addon_keys:
        a = addon_lookup.get(k)
        if a:
            pre_discount += a["price"]
            breakdown.append({"label": f"Add-on · {a['label']}", "amount": a["price"]})

    # --- Property type modifier (cleaning) ---
    property_modifier_pct = 0.0
    if svc.get("category") == "home" and property_type:
        pt = next((p for p in PROPERTY_TYPES if p["key"] == property_type), None)
        if pt and pt["modifier"] > 0:
            property_modifier_pct = pt["modifier"]
            amount = round(pre_discount * property_modifier_pct, 2)
            pre_discount += amount
            breakdown.append({"label": f"{pt['label']} surcharge ({pt['badge']})", "amount": amount})

    # --- Discounts ---
    discount_keys = discount_keys or []
    discount_total = 0.0
    for dk in discount_keys:
        d = DISCOUNTS.get(dk)
        if not d:
            continue
        if svc.get("category") not in d["applies_to_categories"]:
            continue
        amount = round(pre_discount * d["pct"], 2)
        discount_total += amount
        breakdown.append({"label": f"Discount · {d['label']} (−{int(d['pct']*100)}%)", "amount": -amount})

    if first_time_customer:
        amount = round(pre_discount * FIRST_TIME_DISCOUNT_PCT, 2)
        discount_total += amount
        breakdown.append({"label": "Discount - First-time customer offer (-25%)", "amount": -amount})

    after_discount = pre_discount - discount_total

    # --- Advance-booking fee (unchanged) ---
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
    if advance_fee > 0:
        breakdown.append({"label": f"Advance booking fee (≥{ADVANCE_FEE_DAYS} days out)", "amount": advance_fee})

    total = round(after_discount + advance_fee, 2)

    return {
        "base_price": base,
        "advance_fee": advance_fee,
        "discount_total": round(discount_total, 2),
        "property_modifier_pct": property_modifier_pct,
        "first_time_customer_discount": first_time_customer,
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
            "starts_at": _starts_at(svc),
            "tiers": [
                {"key": tk, **tv} for tk, tv in svc.get("tiers", {}).items()
            ],
            "upsells": _service_upsell_meta(key, svc),
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


DEFAULT_DURATION_MIN = 60  # fallback when a service or tier lacks a configured duration


def get_service_duration(service_value: str, tier_key: Optional[str] = None) -> int:
    """Return the duration (in minutes) a service occupies on the calendar."""
    svc = SERVICE_CATALOG.get(service_value)
    if not svc:
        return DEFAULT_DURATION_MIN
    if svc.get("has_tiers"):
        tier = svc["tiers"].get(tier_key) if tier_key else None
        if not tier:
            # fall back to first tier
            try:
                tier = next(iter(svc["tiers"].values()))
            except StopIteration:
                return DEFAULT_DURATION_MIN
        return int(tier.get("duration", DEFAULT_DURATION_MIN))
    return int(svc.get("duration", DEFAULT_DURATION_MIN))


def hhmm_to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def window_minutes() -> tuple:
    return hhmm_to_minutes(BOOKING_TIME_MIN), hhmm_to_minutes(BOOKING_TIME_MAX)

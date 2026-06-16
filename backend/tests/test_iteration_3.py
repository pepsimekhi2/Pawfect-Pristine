"""Iteration 3 backend tests: upsell engine (catalog/upsells, quote stacking, booking persistence).
Also includes regression checks for admin passphrase and service-duration availability blocking.
"""
import os
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or os.environ["REACT_APP_BACKEND_URL"]
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"


# ──────── Fixtures ────────
@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(api_client):
    r = api_client.post(f"{API}/auth/admin-passphrase", json={"passphrase": "duck"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def created_booking_ids():
    return []


# ──────── /api/catalog upsells ────────
class TestCatalogUpsells:
    def test_catalog_has_starts_at_and_upsells(self, api_client):
        r = api_client.get(f"{API}/catalog")
        assert r.status_code == 200
        cat = r.json()
        assert "general_cleaning" in cat and "dog_walking" in cat
        gc = cat["general_cleaning"]
        assert gc["starts_at"] == 15
        u = gc["upsells"]
        # property_types: 3, business modifier 0.30
        keys = {p["key"]: p for p in u["property_types"]}
        assert set(keys) == {"house", "apartment", "business"}
        assert keys["business"]["modifier"] == 0.30
        # room_questions
        assert u["room_questions"]["bedrooms"]["free_units"] == 2
        assert u["room_questions"]["bedrooms"]["price_each"] == 15
        assert u["room_questions"]["bathrooms"]["free_units"] == 1
        assert u["room_questions"]["bathrooms"]["price_each"] == 10
        # cleaning addons: 11 incl move_in_out for general_cleaning
        akeys = {a["key"]: a for a in u["addons"]}
        assert len(u["addons"]) == 11
        for k in ("inside_fridge", "inside_oven", "baseboards", "move_in_out"):
            assert k in akeys
        assert akeys["inside_fridge"]["price"] == 25
        assert akeys["inside_oven"]["price"] == 20
        assert akeys["baseboards"]["price"] == 15
        assert akeys["move_in_out"]["price"] == 50
        # discount byo_supplies
        dkeys = {d["key"]: d for d in u["discounts"]}
        assert "byo_supplies" in dkeys
        assert dkeys["byo_supplies"]["pct"] == 0.15

    def test_catalog_pet_upsells(self, api_client):
        r = api_client.get(f"{API}/catalog")
        cat = r.json()
        dw = cat["dog_walking"]
        u = dw["upsells"]
        assert u["pet_question"]["free_units"] == 1
        assert u["pet_question"]["price_each"] == 5
        assert u["property_types"] == []
        assert u["discounts"] == []  # no discounts apply to pet
        akeys = {a["key"]: a for a in u["addons"]}
        assert len(u["addons"]) == 7
        expected = {"meds": 5, "photos": 3, "plants": 5, "mail": 5, "litter": 5, "bath": 18, "extra_treats": 4}
        for k, price in expected.items():
            assert k in akeys, f"missing pet addon {k}"
            assert akeys[k]["price"] == price


# ──────── /api/quote stacking ────────
class TestQuoteStacking:
    def test_business_with_rooms_addons_discount(self, api_client):
        r = api_client.post(f"{API}/quote", json={
            "service_value": "general_cleaning", "tier_key": "standard",
            "property_type": "business", "bedrooms": 4, "bathrooms": 3,
            "addons": ["inside_fridge", "baseboards"],
            "discounts": ["byo_supplies"],
        })
        assert r.status_code == 200, r.text
        q = r.json()
        # 55 + 2*15 + 2*10 + 25 + 15 = 145; *1.30 = 188.5; -15% = 160.225 → 160.23
        assert q["total"] == 160.23, f"got {q['total']} (breakdown={q['breakdown']})"
        assert q["discount_total"] == 28.27 or q["discount_total"] == 28.28  # rounding
        assert q["property_modifier_pct"] == 0.30

    def test_light_house_no_extras(self, api_client):
        r = api_client.post(f"{API}/quote", json={
            "service_value": "general_cleaning", "tier_key": "light",
            "property_type": "house", "bedrooms": 2, "bathrooms": 1,
        })
        assert r.status_code == 200
        assert r.json()["total"] == 15

    def test_dog_walking_with_pets_and_addons(self, api_client):
        r = api_client.post(f"{API}/quote", json={
            "service_value": "dog_walking", "tier_key": "30",
            "pet_count": 3, "addons": ["meds", "photos"],
        })
        assert r.status_code == 200
        q = r.json()
        # 12 + 2*5 + 5 + 3 = 30
        assert q["total"] == 30, f"got {q['total']} (breakdown={q['breakdown']})"

    def test_standard_with_byo_only(self, api_client):
        r = api_client.post(f"{API}/quote", json={
            "service_value": "general_cleaning", "tier_key": "standard",
            "discounts": ["byo_supplies"],
        })
        assert r.status_code == 200
        # 55 * 0.85 = 46.75
        assert r.json()["total"] == 46.75

    def test_discount_does_not_apply_to_pet(self, api_client):
        """byo_supplies must NOT apply on pet services."""
        r = api_client.post(f"{API}/quote", json={
            "service_value": "dog_walking", "tier_key": "30",
            "discounts": ["byo_supplies"],
        })
        assert r.status_code == 200
        q = r.json()
        assert q["total"] == 12, f"discount must not apply on pet svc — got total={q['total']}"
        assert q["discount_total"] == 0


# ──────── Booking persistence with upsells ────────
class TestBookingUpsellPersistence:
    def test_create_booking_with_upsells_persists(self, api_client, created_booking_ids):
        # Within 7 days → no advance fee, simpler total to assert. Use late slot to avoid clashes.
        date = (datetime.utcnow().date() + timedelta(days=4)).isoformat()
        body = {
            "name": "TEST_Upsell User",
            "phone": "+15555550101",
            "address": "100 Test Ave, Atlanta, GA",
            "service_value": "general_cleaning",
            "tier_key": "standard",
            "preferred_date": date,
            "preferred_time": "16:30",
            "payment_plan": "pay_later",
            "payment_method": "cash",
            "tos_accepted": True,
            "property_type": "business",
            "bedrooms": 4,
            "bathrooms": 3,
            "addons": ["inside_fridge", "baseboards"],
            "discounts": ["byo_supplies"],
        }
        r = api_client.post(f"{API}/bookings", json=body)
        assert r.status_code == 200, r.text
        data = r.json()
        bid = data["id"]
        created_booking_ids.append(bid)
        # grand_total should be 160.23 + travel(0 likely) — accept >=160.23
        assert data["grand_total"] >= 160.23
        assert data["quote"]["total"] == 160.23

    def test_admin_can_read_back_upsell_fields(self, api_client, admin_token, created_booking_ids):
        assert created_booking_ids, "need a booking to verify"
        bid = created_booking_ids[0]
        r = api_client.get(f"{API}/admin/bookings/all",
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        found = next((b for b in r.json() if b["id"] == bid), None)
        assert found is not None
        assert found["property_type"] == "business"
        assert found["bedrooms"] == 4
        assert found["bathrooms"] == 3
        assert "inside_fridge" in found["addons"]
        assert "baseboards" in found["addons"]
        assert "byo_supplies" in found["discounts"]
        assert found["grand_total"] >= 160.23


# ──────── Regression: admin gate & duration blocking ────────
class TestRegression:
    def test_admin_passphrase_duck(self, api_client):
        r = api_client.post(f"{API}/auth/admin-passphrase", json={"passphrase": "duck"})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "admin"

    def test_duration_blocks_overlap(self, api_client, created_booking_ids):
        """Book a 2h standard cleaning at 10:00, verify availability shows 10:00..11:00 taken."""
        date = (datetime.utcnow().date() + timedelta(days=90)).isoformat()
        r = api_client.post(f"{API}/bookings", json={
            "name": "TEST_Dur Block",
            "phone": "+15555550102",
            "address": "200 Test Ave, Atlanta, GA",
            "service_value": "general_cleaning", "tier_key": "standard",
            "preferred_date": date, "preferred_time": "10:00",
            "payment_plan": "pay_later", "payment_method": "cash",
            "tos_accepted": True,
        })
        assert r.status_code == 200, r.text
        created_booking_ids.append(r.json()["id"])
        a = api_client.get(f"{API}/availability",
                           params={"date": date, "service": "dog_walking", "tier": "30"})
        assert a.status_code == 200
        slots = {s["time"]: s for s in a.json()["slots"]}
        for t in ("10:00", "10:30", "11:00", "11:30"):
            assert slots[t]["taken"], f"{t} should be taken (overlap)"
        assert not slots["12:00"]["taken"]


# ──────── Cleanup ────────
def teardown_module(module):
    """Best-effort cleanup of TEST_-prefixed bookings via admin endpoint listing."""
    try:
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        r = s.post(f"{API}/auth/admin-passphrase", json={"passphrase": "duck"})
        if r.status_code != 200:
            return
        # No public delete; rely on Mongo-side cleanup. Just log.
        # (We don't expose a delete endpoint; bookings are left for now.)
    except Exception:
        pass

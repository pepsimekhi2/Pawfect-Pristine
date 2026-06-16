"""Backend tests for Pawfect & Pristine API: /api/eta and /api/bookings"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://task-reserve.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _post_eta(address, retries=1):
    last = None
    for _ in range(retries + 1):
        try:
            r = requests.post(f"{API}/eta", json={"address": address}, timeout=30)
            last = r
            if r.status_code in (200, 400, 404, 502):
                return r
        except requests.RequestException as e:
            last = e
        time.sleep(2)
    return last


# ---------- ETA tests ----------
class TestETA:
    def test_eta_health(self):
        r = requests.get(f"{API}/", timeout=10)
        assert r.status_code == 200
        assert "Pawfect" in r.json().get("message", "")

    def test_eta_standard_nearby_atlanta(self):
        r = _post_eta("Atlanta, GA 30308", retries=1)
        assert r.status_code == 200, f"Body: {r.text}"
        d = r.json()
        for k in ("distance_miles", "duration_minutes", "arrival_window",
                  "zone", "extra_fee", "zone_message", "resolved_address",
                  "zone_label", "arrival_time"):
            assert k in d, f"Missing {k} in {d}"
        # 30308 is downtown ATL — should be standard (<=7mi from Decatur)
        assert d["zone"] == "standard"
        assert d["extra_fee"] == 0
        assert d["distance_miles"] > 0
        assert d["duration_minutes"] > 0
        assert len(d["zone_message"]) > 0
        assert len(d["resolved_address"]) > 0

    def test_eta_extended_or_classified_correctly(self):
        r = _post_eta("Tucker, GA 30084", retries=1)
        assert r.status_code == 200, f"Body: {r.text}"
        d = r.json()
        miles = d["distance_miles"]
        if miles <= 7:
            assert d["zone"] == "standard" and d["extra_fee"] == 0
        elif miles <= 13:
            assert d["zone"] == "extended" and d["extra_fee"] == 20
        else:
            assert d["zone"] == "out_of_range" and d["extra_fee"] == 0

    def test_eta_out_of_range_marietta(self):
        r = _post_eta("Marietta, GA 30060", retries=1)
        assert r.status_code == 200, f"Body: {r.text}"
        d = r.json()
        # Marietta should be ~20+ miles from Decatur
        assert d["distance_miles"] > 13, f"Expected >13mi, got {d['distance_miles']}"
        assert d["zone"] == "out_of_range"
        assert d["extra_fee"] == 0
        assert "470" in d["zone_message"] and "381-4682" in d["zone_message"]

    def test_eta_empty_address(self):
        r = requests.post(f"{API}/eta", json={"address": ""}, timeout=15)
        assert r.status_code == 400

    def test_eta_gibberish_address(self):
        r = _post_eta("zzzzzqqqq nowhere fake place 99999", retries=1)
        assert r.status_code == 404
        d = r.json()
        assert "detail" in d
        assert len(d["detail"]) > 0


# ---------- Bookings tests ----------
class TestBookings:
    created_id = None

    def test_create_booking_full_payload(self):
        payload = {
            "name": "TEST_User",
            "phone": "4045550123",
            "address": "Atlanta, GA",
            "service_category": "home",
            "service_type": "General Cleaning",
            "bedrooms": 2,
            "bathrooms": 1,
            "pets": 0,
            "preferred_date": "Sat",
            "preferred_time": "2pm",
        }
        r = requests.post(f"{API}/bookings", json=payload, timeout=45)
        assert r.status_code == 200, f"Body: {r.text}"
        d = r.json()
        assert "id" in d and isinstance(d["id"], str) and len(d["id"]) > 0
        assert "sms_sent" in d and isinstance(d["sms_sent"], bool)
        assert "message" in d and len(d["message"]) > 0
        # eta may be None if external service hiccupped, but key must be present
        assert "eta" in d
        if d["eta"]:
            for k in ("distance_miles", "duration_minutes", "zone", "extra_fee"):
                assert k in d["eta"]
        TestBookings.created_id = d["id"]

    def test_recent_bookings_lists_created(self):
        # Make sure we have created a booking
        assert TestBookings.created_id, "Previous booking creation failed"
        r = requests.get(f"{API}/bookings/recent", timeout=15)
        assert r.status_code == 200
        bookings = r.json()
        assert isinstance(bookings, list)
        # No _id leakage
        for b in bookings:
            assert "_id" not in b
        # Find our booking
        ids = [b.get("id") for b in bookings]
        assert TestBookings.created_id in ids, "Created id not found in recent list"

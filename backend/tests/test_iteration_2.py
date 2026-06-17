"""Iteration 2 — admin passphrase, service durations, overlap blocking, sms_link."""
import os
import time
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote_plus

BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")

ADMIN_EMAIL = "admin@pawfectpristine.com"
ADMIN_PASSWORD = "Pawfect2026!"
PASSPHRASE = "duck"

# Use a fixed future date well clear of today
FUTURE_DATE = (datetime.now(timezone.utc) + timedelta(days=14)).date().isoformat()


def _admin_token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


def _admin_headers():
    return {"Authorization": f"Bearer {_admin_token()}"}


# -------- 1. Catalog durations --------
def test_catalog_durations():
    r = requests.get(f"{BASE}/api/catalog", timeout=15)
    assert r.status_code == 200
    cat = r.json()
    checks = [
        ("general_cleaning", "light", 60),
        ("general_cleaning", "heavy", 180),
        ("deep_cleaning", "large", 360),
        ("pet_sitting", "overnight", 720),
        ("dog_walking", "30", 30),
    ]
    for svc, tier_key, expected in checks:
        tiers = cat[svc]["tiers"]
        match = next((t for t in tiers if t["key"] == tier_key), None)
        assert match is not None, f"{svc}.{tier_key} missing"
        assert match.get("duration") == expected, f"{svc}.{tier_key} duration = {match.get('duration')} != {expected}"


# -------- 2. Admin passphrase --------
def test_passphrase_correct():
    r = requests.post(f"{BASE}/api/auth/admin-passphrase", json={"passphrase": PASSPHRASE}, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "token" in data
    assert data["user"]["role"] == "admin"


def test_passphrase_wrong():
    # Use unique wrong str to avoid brute force counter polluting other tests on same IP
    r = requests.post(f"{BASE}/api/auth/admin-passphrase",
                      json={"passphrase": "definitely-not-it-xyz"}, timeout=15)
    assert r.status_code in (401, 429), r.text


def test_passphrase_brute_force_429():
    # Hammer wrong attempts; brute-force shared with login_attempts collection identified by ip:admin-passphrase
    # Kube ingress load-balances across multiple backend pods, each tracking attempts
    # independently. Hammer enough requests that at least one pod gets locked out.
    saw_429 = False
    for i in range(40):
        r = requests.post(f"{BASE}/api/auth/admin-passphrase",
                          json={"passphrase": f"wrong-{i}"}, timeout=15)
        if r.status_code == 429:
            saw_429 = True
            break
        time.sleep(0.05)
    assert saw_429, "Expected at least one 429 after 40 wrong attempts (brute force protection per backend pod)"


# -------- 3. Availability too_late --------
def test_availability_too_late_for_large_deep():
    r = requests.get(f"{BASE}/api/availability",
                     params={"date": FUTURE_DATE, "service": "deep_cleaning", "tier": "large"}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["duration_minutes"] == 360
    by_time = {s["time"]: s for s in data["slots"]}
    # 13:00 itself should be allowed (13:00 + 360 = 19:00 = max 18:30 + 30 cap)
    assert "13:00" in by_time
    assert by_time["13:00"]["too_late"] is False, f"13:00 too_late should be False: {by_time['13:00']}"
    # 13:30 and onwards should be too_late
    for t in ["13:30", "14:00", "15:00", "17:00", "18:30"]:
        if t in by_time:
            assert by_time[t]["too_late"] is True, f"{t} too_late should be True: {by_time[t]}"


# -------- 4. Overlap blocking --------
created_booking_id = {"id": None}


def test_create_booking_and_overlap_block():
    # Use unique future date so we own the timeline
    test_date = (datetime.now(timezone.utc) + timedelta(days=21)).date().isoformat()
    payload = {
        "name": "TEST_Overlap_User",
        "phone": "+15551234567",
        "address": "123 Test St, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "standard",  # 120 min
        "preferred_date": test_date,
        "preferred_time": "10:00",
        "payment_plan": "pay_later",
        "payment_method": "later",
        "tos_accepted": True,
        "access_method": "home",
    }
    r = requests.post(f"{BASE}/api/bookings", json=payload, timeout=30)
    assert r.status_code == 200, f"create failed: {r.status_code} {r.text}"
    bid = r.json()["id"]
    created_booking_id["id"] = bid
    created_booking_id["date"] = test_date

    # Check availability — 30min dog_walking
    r2 = requests.get(f"{BASE}/api/availability",
                      params={"date": test_date, "service": "dog_walking", "tier": "30"}, timeout=15)
    assert r2.status_code == 200
    by_time = {s["time"]: s for s in r2.json()["slots"]}
    for t in ["10:00", "10:30", "11:00", "11:30"]:
        assert by_time[t]["taken"] is True, f"{t} should be taken (overlap with 10:00 standard 120min): {by_time[t]}"
    # 12:00 should be free again
    assert by_time["12:00"]["taken"] is False, f"12:00 should be free: {by_time['12:00']}"

    # Attempt second booking at 10:30 — should 409
    payload2 = {**payload, "preferred_time": "10:30", "name": "TEST_Overlap_User2",
                "service_value": "dog_walking", "tier_key": "30"}
    r3 = requests.post(f"{BASE}/api/bookings", json=payload2, timeout=30)
    assert r3.status_code == 409, f"expected 409 overlap, got {r3.status_code}: {r3.text}"
    assert "overlap" in r3.json().get("detail", "").lower()


def test_window_past_close_400():
    payload = {
        "name": "TEST_PastClose",
        "phone": "+15551234567",
        "address": "123 Test St, Decatur, GA",
        "service_value": "deep_cleaning",
        "tier_key": "large",  # 360 min
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat(),
        "preferred_time": "14:00",  # 14:00 + 360 = 20:00 > 19:00 cap
        "payment_plan": "pay_later",
        "payment_method": "later",
        "tos_accepted": True,
        "access_method": "home",
    }
    r = requests.post(f"{BASE}/api/bookings", json=payload, timeout=30)
    assert r.status_code == 400, f"expected 400 past-close, got {r.status_code}: {r.text}"
    assert "close" in r.json().get("detail", "").lower()


# -------- 5. Admin reschedule overlap --------
def test_admin_reschedule_overlap_409():
    h = _admin_headers()
    test_date = (datetime.now(timezone.utc) + timedelta(days=35)).date().isoformat()

    # Two non-conflicting bookings at 09:00 (dog_walking 30) and 14:00 (dog_walking 30)
    bookings_created = []
    for t in ["09:00", "14:00"]:
        payload = {
            "name": f"TEST_Reschedule_{t}",
            "phone": "+15551234567",
            "address": "123 Test St, Decatur, GA",
            "service_value": "dog_walking",
            "tier_key": "30",
            "preferred_date": test_date,
            "preferred_time": t,
            "payment_plan": "pay_later",
            "payment_method": "later",
            "tos_accepted": True,
            "access_method": "home",
        }
        r = requests.post(f"{BASE}/api/bookings", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        bookings_created.append(r.json()["id"])

    try:
        # Reschedule first onto second's slot — should 409
        r = requests.post(f"{BASE}/api/admin/bookings/{bookings_created[0]}/reschedule",
                          json={"preferred_date": test_date, "preferred_time": "14:00"},
                          headers=h, timeout=15)
        assert r.status_code == 409, f"expected 409, got {r.status_code}: {r.text}"
    finally:
        # Cleanup
        for bid in bookings_created:
            requests.post(f"{BASE}/api/admin/bookings/{bid}/cancel", headers=h, timeout=15)


# -------- 6. Notify-OTW sms_link --------
def test_notify_otw_sms_link():
    h = _admin_headers()
    test_date = (datetime.now(timezone.utc) + timedelta(days=40)).date().isoformat()
    payload = {
        "name": "TEST_OTW",
        "phone": "+15557654321",
        "address": "1 Main St, Decatur, GA",
        "service_value": "dog_walking",
        "tier_key": "30",
        "preferred_date": test_date,
        "preferred_time": "11:00",
        "payment_plan": "pay_later",
        "payment_method": "later",
        "tos_accepted": True,
        "access_method": "home",
    }
    r = requests.post(f"{BASE}/api/bookings", json=payload, timeout=30)
    assert r.status_code == 200
    bid = r.json()["id"]

    try:
        r2 = requests.post(f"{BASE}/api/admin/bookings/{bid}/notify-otw", headers=h, timeout=15)
        assert r2.status_code == 200, r2.text
        data = r2.json()
        assert "sms_link" in data
        link = data["sms_link"]
        assert link.startswith("sms:+15557654321"), f"sms_link prefix wrong: {link}"
        assert "?&body=" in link
        body_enc = link.split("?&body=", 1)[1]
        decoded = unquote_plus(body_enc)
        assert "Pawfect" in decoded
        assert "TEST_OTW" in decoded
        assert "tel_link" in data
        assert data["tel_link"] == "tel:+15557654321"
    finally:
        requests.post(f"{BASE}/api/admin/bookings/{bid}/cancel", headers=h, timeout=15)


# -------- 7. Existing admin flows --------
def test_admin_stats_and_lists():
    h = _admin_headers()
    for path in ["/api/admin/stats", "/api/admin/bookings/today", "/api/admin/bookings/upcoming",
                 "/api/admin/customers"]:
        r = requests.get(f"{BASE}{path}", headers=h, timeout=15)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text}"
    stats = requests.get(f"{BASE}/api/admin/stats", headers=h, timeout=15).json()
    for k in ["today_bookings", "today_revenue", "upcoming_count", "customers_count"]:
        assert k in stats


# -------- Cleanup --------
def test_zz_cleanup_overlap_booking():
    bid = created_booking_id.get("id")
    if not bid:
        return
    h = _admin_headers()
    r = requests.post(f"{BASE}/api/admin/bookings/{bid}/cancel", headers=h, timeout=15)
    assert r.status_code == 200

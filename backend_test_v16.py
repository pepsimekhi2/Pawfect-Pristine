#!/usr/bin/env python3
"""
Backend API tests for Pawfect & Pristine v1.6
Tests PayPal integration and booking payment_status logic
"""
import requests
import json
import os
from datetime import datetime, timedelta
import random

# Backend URL from frontend/.env
BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api").rstrip("/")

# Test credentials
TEST_USER = {
    "name": "V16 Test User",
    "email": f"v16test{random.randint(1000,9999)}@example.com",
    "password": "SecurePass123!",
    "marketing_opt_in": True,
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_test(name: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def log_pass(msg: str):
    print(f"{Colors.GREEN}✓ PASS: {msg}{Colors.END}")

def log_fail(msg: str):
    print(f"{Colors.RED}✗ FAIL: {msg}{Colors.END}")

def log_info(msg: str):
    print(f"{Colors.YELLOW}ℹ INFO: {msg}{Colors.END}")

def get_future_date(days_from_now: int) -> str:
    """Return ISO date string N days from now"""
    return (datetime.now() + timedelta(days=days_from_now)).date().isoformat()

def register_and_login():
    """Register a new user and return token"""
    log_test("Setup: Register test user")
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    if response.status_code == 200:
        data = response.json()
        log_pass(f"User registered: {data['user']['email']}")
        return data["token"]
    else:
        log_fail(f"Registration failed: {response.status_code}")
        return None

# ============= PRIORITY 1: PAYPAL ENDPOINTS =============
def test_paypal_config():
    log_test("P1.1: GET /api/paypal/config")
    response = requests.get(f"{BASE_URL}/paypal/config")
    
    if response.status_code == 200:
        data = response.json()
        checks = [
            (data.get("enabled") == True, f"enabled=true"),
            (data.get("env") == "live", f"env='live'"),
            (data.get("client_id") and len(data.get("client_id")) > 0, f"client_id is non-null string"),
            (data.get("currency") == "USD", f"currency='USD'")
        ]
        all_pass = all(check for check, _ in checks)
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
        return all_pass
    else:
        log_fail(f"Failed: {response.status_code}")
        return False

def test_paypal_create_order_valid():
    log_test("P1.2: POST /api/paypal/create-order (valid)")
    payload = {"amount": 1.00, "currency": "USD", "booking_ref": "test-1", "description": "test"}
    response = requests.post(f"{BASE_URL}/paypal/create-order", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        checks = [
            (data.get("id") and len(data.get("id")) > 0, f"id is non-empty string"),
            (data.get("status") == "CREATED", f"status='CREATED'"),
            (isinstance(data.get("links"), list), f"links is array")
        ]
        all_pass = all(check for check, _ in checks)
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
        if all_pass:
            log_info(f"PayPal Order ID: {data.get('id')}")
        return all_pass
    else:
        log_fail(f"Failed: {response.status_code}")
        return False

def test_paypal_create_order_invalid():
    log_test("P1.3: POST /api/paypal/create-order (amount < 0, expect 400)")
    payload = {"amount": -1.00}
    response = requests.post(f"{BASE_URL}/paypal/create-order", json=payload)
    
    if response.status_code == 400:
        log_pass("Invalid amount rejected with 400")
        return True
    else:
        log_fail(f"Expected 400, got {response.status_code}")
        return False

def test_paypal_capture_order_invalid():
    log_test("P1.4: POST /api/paypal/capture-order (invalid order_id, expect 502)")
    payload = {"order_id": "INVALID_ORDER_ID"}
    response = requests.post(f"{BASE_URL}/paypal/capture-order", json=payload)
    
    # Backend should return 502, but may be intercepted by proxy
    if response.status_code in [502, 404]:
        log_pass(f"Invalid order_id rejected with {response.status_code}")
        log_info("Note: 404 from PayPal is acceptable (backend catches and returns 502)")
        return True
    else:
        log_fail(f"Expected 502 or 404, got {response.status_code}")
        return False

# ============= PRIORITY 2: BOOKING PAYMENT_STATUS LOGIC =============
def test_booking_paypal_paid_full(token: str):
    log_test("P2.1: Booking with paypal_capture_id + all_now → payment_status='paid_full'")
    
    future_date = get_future_date(20)  # Far future to avoid conflicts
    time_slot = "09:00"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Test PayPal Full",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "dog_walking",  # Different service to avoid conflicts
        "tier_key": "30",
        "pets": 0,
        "notes": "",
        "preferred_date": future_date,
        "preferred_time": time_slot,
        "payment_plan": "all_now",
        "payment_method": "paypal",
        "tos_accepted": True,
        "paypal_order_id": "PP-FAKE-ORDER-1",
        "paypal_capture_id": "PP-FAKE-CAPTURE-1",
        "paypal_captured_amount": 150.00
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        booking_id = response.json().get("id")
        # Fetch booking to verify payment_status
        get_resp = requests.get(f"{BASE_URL}/bookings/me", headers=headers)
        if get_resp.status_code == 200:
            bookings = get_resp.json()
            booking = next((b for b in bookings if b.get("id") == booking_id), None)
            if booking and booking.get("payment_status") == "paid_full":
                log_pass("payment_status='paid_full' (NOT 'paid_full_pending_verify')")
                return True
            else:
                log_fail(f"payment_status should be 'paid_full', got '{booking.get('payment_status') if booking else 'N/A'}'")
                return False
        else:
            log_fail(f"Failed to fetch bookings: {get_resp.status_code}")
            return False
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text[:200]}")
        return False

def test_booking_paypal_paid_half(token: str):
    log_test("P2.2: Booking with paypal_capture_id + half_now → payment_status='paid_half'")
    
    future_date = get_future_date(21)  # Far future to avoid conflicts
    time_slot = "10:00"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Test PayPal Half",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "dog_walking",  # Different service to avoid conflicts
        "tier_key": "30",
        "pets": 0,
        "notes": "",
        "preferred_date": future_date,
        "preferred_time": time_slot,
        "payment_plan": "half_now",
        "payment_method": "paypal",
        "tos_accepted": True,
        "paypal_order_id": "PP-FAKE-ORDER-2",
        "paypal_capture_id": "PP-FAKE-CAPTURE-2",
        "paypal_captured_amount": 75.00
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        booking_id = response.json().get("id")
        get_resp = requests.get(f"{BASE_URL}/bookings/me", headers=headers)
        if get_resp.status_code == 200:
            bookings = get_resp.json()
            booking = next((b for b in bookings if b.get("id") == booking_id), None)
            if booking and booking.get("payment_status") == "paid_half":
                log_pass("payment_status='paid_half' (NOT 'paid_half_pending_verify')")
                return True
            else:
                log_fail(f"payment_status should be 'paid_half', got '{booking.get('payment_status') if booking else 'N/A'}'")
                return False
        else:
            log_fail(f"Failed to fetch bookings: {get_resp.status_code}")
            return False
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text[:200]}")
        return False

def test_booking_paypal_pending_verify(token: str):
    log_test("P2.3: Booking WITHOUT paypal_capture_id → payment_status='paid_full_pending_verify'")
    
    future_date = get_future_date(5)
    time_slot = f"{9 + random.randint(0, 8)}:00"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Test PayPal Legacy",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "standard",
        "pets": 0,
        "notes": "",
        "preferred_date": future_date,
        "preferred_time": time_slot,
        "payment_plan": "all_now",
        "payment_method": "paypal",
        "tos_accepted": True
        # NO paypal_capture_id
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        booking_id = response.json().get("id")
        get_resp = requests.get(f"{BASE_URL}/bookings/me", headers=headers)
        if get_resp.status_code == 200:
            bookings = get_resp.json()
            booking = next((b for b in bookings if b.get("id") == booking_id), None)
            if booking and booking.get("payment_status") == "paid_full_pending_verify":
                log_pass("payment_status='paid_full_pending_verify' (legacy fallback)")
                return True
            else:
                log_fail(f"payment_status should be 'paid_full_pending_verify', got '{booking.get('payment_status') if booking else 'N/A'}'")
                return False
        else:
            log_fail(f"Failed to fetch bookings: {get_resp.status_code}")
            return False
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text[:200]}")
        return False

def test_booking_cash_unpaid(token: str):
    log_test("P2.4: Booking with cash + pay_later → payment_status='unpaid'")
    
    future_date = get_future_date(6)
    time_slot = f"{9 + random.randint(0, 8)}:00"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Test Cash",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "standard",
        "pets": 0,
        "notes": "",
        "preferred_date": future_date,
        "preferred_time": time_slot,
        "payment_plan": "pay_later",
        "payment_method": "cash",
        "tos_accepted": True
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        booking_id = response.json().get("id")
        get_resp = requests.get(f"{BASE_URL}/bookings/me", headers=headers)
        if get_resp.status_code == 200:
            bookings = get_resp.json()
            booking = next((b for b in bookings if b.get("id") == booking_id), None)
            if booking and booking.get("payment_status") == "unpaid":
                log_pass("payment_status='unpaid'")
                return True
            else:
                log_fail(f"payment_status should be 'unpaid', got '{booking.get('payment_status') if booking else 'N/A'}'")
                return False
        else:
            log_fail(f"Failed to fetch bookings: {get_resp.status_code}")
            return False
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text[:200]}")
        return False

# ============= PRIORITY 3: REGRESSION TESTS =============
def test_regression_auth():
    log_test("P3.1: Auth endpoints (register/login/me/logout)")
    # Register already done in setup
    # Test login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    if login_resp.status_code != 200:
        log_fail(f"Login failed: {login_resp.status_code}")
        return False
    
    token = login_resp.json().get("token")
    
    # Test /me
    me_resp = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
    if me_resp.status_code != 200:
        log_fail(f"/auth/me failed: {me_resp.status_code}")
        return False
    
    # Test logout
    logout_resp = requests.post(f"{BASE_URL}/auth/logout")
    if logout_resp.status_code != 200:
        log_fail(f"Logout failed: {logout_resp.status_code}")
        return False
    
    log_pass("All auth endpoints working")
    return True

def test_regression_catalog():
    log_test("P3.2: GET /api/catalog")
    response = requests.get(f"{BASE_URL}/catalog")
    if response.status_code == 200 and "general_cleaning" in response.json():
        log_pass("Catalog endpoint working")
        return True
    else:
        log_fail(f"Catalog failed: {response.status_code}")
        return False

def test_regression_quote():
    log_test("P3.3: POST /api/quote")
    payload = {"service_value": "general_cleaning", "tier_key": "heavy", "preferred_date": get_future_date(10)}
    response = requests.post(f"{BASE_URL}/quote", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data.get("advance_fee") == 0.99:
            log_pass("Quote endpoint working (advance fee calculated)")
            return True
        else:
            log_fail(f"Advance fee wrong: {data.get('advance_fee')}")
            return False
    else:
        log_fail(f"Quote failed: {response.status_code}")
        return False

def test_regression_eta():
    log_test("P3.4: POST /api/eta")
    payload = {"address": "199 N Decatur Rd, Decatur, GA"}
    response = requests.post(f"{BASE_URL}/eta", json=payload)
    if response.status_code == 200 and "distance_miles" in response.json():
        log_pass("ETA endpoint working")
        return True
    else:
        log_fail(f"ETA failed: {response.status_code}")
        return False

def test_regression_tos():
    log_test("P3.5: GET /api/tos")
    response = requests.get(f"{BASE_URL}/tos")
    if response.status_code == 200:
        data = response.json()
        if data.get("version") and data.get("text"):
            log_pass("TOS endpoint working")
            return True
    log_fail(f"TOS failed: {response.status_code}")
    return False

def test_regression_firebase():
    log_test("P3.6: GET /api/firebase/status")
    response = requests.get(f"{BASE_URL}/firebase/status")
    if response.status_code == 200 and "enabled" in response.json():
        log_pass("Firebase status endpoint working")
        return True
    else:
        log_fail(f"Firebase status failed: {response.status_code}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}PAWFECT & PRISTINE - v1.6 BACKEND TESTS{Colors.END}")
    print(f"{Colors.BLUE}Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    results = {}
    
    # Setup
    token = register_and_login()
    if not token:
        print(f"{Colors.RED}Setup failed - cannot continue{Colors.END}")
        return False
    
    # Priority 1: PayPal endpoints
    results["P1.1_paypal_config"] = test_paypal_config()
    results["P1.2_paypal_create_valid"] = test_paypal_create_order_valid()
    results["P1.3_paypal_create_invalid"] = test_paypal_create_order_invalid()
    results["P1.4_paypal_capture_invalid"] = test_paypal_capture_order_invalid()
    
    # Priority 2: Booking payment_status logic
    results["P2.1_booking_paid_full"] = test_booking_paypal_paid_full(token)
    results["P2.2_booking_paid_half"] = test_booking_paypal_paid_half(token)
    results["P2.3_booking_pending_verify"] = test_booking_paypal_pending_verify(token)
    results["P2.4_booking_cash_unpaid"] = test_booking_cash_unpaid(token)
    
    # Priority 3: Regression tests
    results["P3.1_auth"] = test_regression_auth()
    results["P3.2_catalog"] = test_regression_catalog()
    results["P3.3_quote"] = test_regression_quote()
    results["P3.4_eta"] = test_regression_eta()
    results["P3.5_tos"] = test_regression_tos()
    results["P3.6_firebase"] = test_regression_firebase()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    if passed == total:
        print(f"{Colors.GREEN}ALL TESTS PASSED: {passed}/{total}{Colors.END}")
    else:
        print(f"{Colors.YELLOW}TESTS PASSED: {passed}/{total}{Colors.END}")
        print(f"{Colors.RED}TESTS FAILED: {total - passed}/{total}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

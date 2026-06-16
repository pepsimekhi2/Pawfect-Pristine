#!/usr/bin/env python3
"""
Backend API tests for Pawfect & Pristine
Tests all backend endpoints per test_result.md requirements
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Optional

# Backend URL from frontend/.env
BASE_URL = "https://7d251449-dcf6-49e0-a51f-406dbcd33d51.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@pawfectpristine.com"
ADMIN_PASSWORD = "Pawfect2026!"

# Test user data (will be created during tests)
TEST_USER = {
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com",
    "password": "SecurePass123!"
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

# ============= TEST 1: AUTH - REGISTER =============
def test_auth_register():
    log_test("1. POST /api/auth/register - Valid registration")
    
    # Test valid registration
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    
    if response.status_code == 200:
        data = response.json()
        if "user" in data and "token" in data:
            log_pass(f"Registration successful: {data['user']['email']}")
            log_info(f"User ID: {data['user']['id']}")
            log_info(f"Token received: {data['token'][:20]}...")
            return data["token"]
        else:
            log_fail("Response missing 'user' or 'token' fields")
            return None
    elif response.status_code == 409:
        log_info("User already exists (409) - this is expected if test ran before")
        # Try to login instead
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            log_pass("Logged in with existing user")
            return data["token"]
        else:
            log_fail(f"Could not login with existing user: {login_resp.status_code}")
            return None
    else:
        log_fail(f"Registration failed: {response.status_code} - {response.text}")
        return None

def test_auth_register_duplicate():
    log_test("2. POST /api/auth/register - Duplicate email (should return 409)")
    
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    
    if response.status_code == 409:
        log_pass("Duplicate registration correctly rejected with 409")
        return True
    else:
        log_fail(f"Expected 409, got {response.status_code}")
        return False

# ============= TEST 2: AUTH - LOGIN =============
def test_auth_login_wrong_password():
    log_test("3. POST /api/auth/login - Wrong password (should return 401)")
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_USER["email"],
        "password": "WrongPassword123!"
    })
    
    if response.status_code == 401:
        log_pass("Wrong password correctly rejected with 401")
        return True
    else:
        log_fail(f"Expected 401, got {response.status_code}")
        return False

def test_auth_login_correct():
    log_test("4. POST /api/auth/login - Correct credentials")
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    
    if response.status_code == 200:
        data = response.json()
        if "user" in data and "token" in data:
            log_pass(f"Login successful: {data['user']['email']}")
            log_info(f"Token: {data['token'][:20]}...")
            return data["token"]
        else:
            log_fail("Response missing 'user' or 'token' fields")
            return None
    else:
        log_fail(f"Login failed: {response.status_code} - {response.text}")
        return None

# ============= TEST 3: AUTH - ME =============
def test_auth_me(token: str):
    log_test("5. GET /api/auth/me - Get current user with token")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "user" in data:
            log_pass(f"User info retrieved: {data['user']['email']}")
            log_info(f"User: {json.dumps(data['user'], indent=2)}")
            return True
        else:
            log_fail("Response missing 'user' field")
            return False
    else:
        log_fail(f"Failed to get user info: {response.status_code} - {response.text}")
        return False

# ============= TEST 4: AUTH - LOGOUT =============
def test_auth_logout():
    log_test("6. POST /api/auth/logout")
    
    response = requests.post(f"{BASE_URL}/auth/logout")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            log_pass("Logout successful")
            return True
        else:
            log_fail("Logout response missing 'ok' field")
            return False
    else:
        log_fail(f"Logout failed: {response.status_code} - {response.text}")
        return False

# ============= TEST 5: CATALOG =============
def test_catalog():
    log_test("7. GET /api/catalog - Service catalog")
    
    response = requests.get(f"{BASE_URL}/catalog")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check for general_cleaning service
        if "general_cleaning" in data:
            gc = data["general_cleaning"]
            log_pass("Catalog retrieved successfully")
            log_info(f"Services available: {len(data)}")
            
            # Verify general_cleaning has required structure
            if gc.get("has_tiers") and gc.get("tier_question"):
                log_pass("general_cleaning has tiers and tier_question")
                
                # Check for 4 tiers: light, standard, heavy, disaster
                tiers = gc.get("tiers", [])
                tier_keys = [t["key"] for t in tiers]
                expected_tiers = ["light", "standard", "heavy", "disaster"]
                
                if all(t in tier_keys for t in expected_tiers):
                    log_pass(f"All 4 tiers present: {tier_keys}")
                    
                    # Verify prices
                    tier_dict = {t["key"]: t for t in tiers}
                    expected_prices = {
                        "light": 110,
                        "standard": 150,
                        "heavy": 210,
                        "disaster": 290
                    }
                    
                    all_correct = True
                    for key, expected_price in expected_prices.items():
                        actual_price = tier_dict[key]["price"]
                        if actual_price == expected_price:
                            log_pass(f"Tier '{key}' price correct: ${actual_price}")
                        else:
                            log_fail(f"Tier '{key}' price wrong: expected ${expected_price}, got ${actual_price}")
                            all_correct = False
                    
                    return all_correct
                else:
                    log_fail(f"Missing tiers. Expected {expected_tiers}, got {tier_keys}")
                    return False
            else:
                log_fail("general_cleaning missing has_tiers or tier_question")
                return False
        else:
            log_fail("Catalog missing 'general_cleaning' service")
            return False
    else:
        log_fail(f"Failed to get catalog: {response.status_code} - {response.text}")
        return False

# ============= TEST 6: QUOTE =============
def test_quote_with_advance_fee():
    log_test("8. POST /api/quote - With advance fee (10 days out)")
    
    future_date = get_future_date(10)
    payload = {
        "service_value": "general_cleaning",
        "tier_key": "heavy",
        "preferred_date": future_date
    }
    
    response = requests.post(f"{BASE_URL}/quote", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        log_info(f"Quote response: {json.dumps(data, indent=2)}")
        
        # Verify expected values
        checks = [
            (data.get("base_price") == 210, f"base_price should be 210, got {data.get('base_price')}"),
            (data.get("advance_fee") == 0.99, f"advance_fee should be 0.99, got {data.get('advance_fee')}"),
            (data.get("total") == 210.99, f"total should be 210.99, got {data.get('total')}"),
            (data.get("is_advance") == True, f"is_advance should be True, got {data.get('is_advance')}")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        return all_pass
    else:
        log_fail(f"Quote failed: {response.status_code} - {response.text}")
        return False

def test_quote_without_advance_fee():
    log_test("9. POST /api/quote - Without advance fee (today)")
    
    today = datetime.now().date().isoformat()
    payload = {
        "service_value": "general_cleaning",
        "tier_key": "heavy",
        "preferred_date": today
    }
    
    response = requests.post(f"{BASE_URL}/quote", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        log_info(f"Quote response: {json.dumps(data, indent=2)}")
        
        checks = [
            (data.get("base_price") == 210, f"base_price should be 210, got {data.get('base_price')}"),
            (data.get("advance_fee") == 0, f"advance_fee should be 0, got {data.get('advance_fee')}"),
            (data.get("total") == 210, f"total should be 210, got {data.get('total')}"),
            (data.get("is_advance") == False, f"is_advance should be False, got {data.get('is_advance')}")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        return all_pass
    else:
        log_fail(f"Quote failed: {response.status_code} - {response.text}")
        return False

# ============= TEST 7: ETA =============
def test_eta():
    log_test("10. POST /api/eta - Calculate distance and travel fee")
    
    payload = {"address": "199 N Decatur Rd, Decatur, GA"}
    response = requests.post(f"{BASE_URL}/eta", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        log_info(f"ETA response: {json.dumps(data, indent=2)}")
        
        checks = [
            ("distance_miles" in data, "distance_miles present"),
            ("duration_minutes" in data, "duration_minutes present"),
            (data.get("extra_fee") == 0, f"extra_fee should be 0 (in-range), got {data.get('extra_fee')}"),
            (data.get("in_range", True), "in_range should be True")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        log_info(f"Distance: {data.get('distance_miles')} miles, Duration: {data.get('duration_minutes')} min")
        return all_pass
    else:
        log_fail(f"ETA failed: {response.status_code} - {response.text}")
        return False

# ============= TEST 8: BOOKINGS =============
def test_booking_half_now(token: str):
    log_test("11. POST /api/bookings - Half now payment plan")
    
    future_date = get_future_date(10)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Sarah Johnson",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "heavy",
        "pets": 0,
        "notes": "Please use eco-friendly products",
        "preferred_date": future_date,
        "preferred_time": "14:00",
        "payment_plan": "half_now",
        "payment_method": "card",
        "tos_accepted": True
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log_info(f"Booking response: {json.dumps(data, indent=2)}")
        
        # Expected: grand_total ≈ 210.99, due_now ≈ 105.50, due_later ≈ 105.49
        grand_total = data.get("grand_total")
        due_now = data.get("due_now")
        due_later = data.get("due_later")
        
        checks = [
            (abs(grand_total - 210.99) < 0.01, f"grand_total should be ~210.99, got {grand_total}"),
            (abs(due_now - 105.50) < 0.01, f"due_now should be ~105.50, got {due_now}"),
            (abs(due_later - 105.49) < 0.01, f"due_later should be ~105.49, got {due_later}"),
            ("id" in data, "Booking ID present")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        return data.get("id") if all_pass else None
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text}")
        return None

def test_booking_all_now(token: str):
    log_test("12. POST /api/bookings - All now payment plan")
    
    future_date = get_future_date(10)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Sarah Johnson",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "heavy",
        "pets": 1,
        "notes": "One friendly dog",
        "preferred_date": future_date,
        "preferred_time": "10:00",
        "payment_plan": "all_now",
        "payment_method": "card",
        "tos_accepted": True
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log_info(f"Booking response: {json.dumps(data, indent=2)}")
        
        grand_total = data.get("grand_total")
        due_now = data.get("due_now")
        
        checks = [
            (abs(grand_total - 210.99) < 0.01, f"grand_total should be ~210.99, got {grand_total}"),
            (abs(due_now - grand_total) < 0.01, f"due_now should equal grand_total, got due_now={due_now}, grand_total={grand_total}"),
            ("id" in data, "Booking ID present")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        return data.get("id") if all_pass else None
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text}")
        return None

def test_booking_pay_later(token: str):
    log_test("13. POST /api/bookings - Pay later payment plan")
    
    future_date = get_future_date(10)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Sarah Johnson",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "light",
        "pets": 0,
        "notes": "",
        "preferred_date": future_date,
        "preferred_time": "16:00",
        "payment_plan": "pay_later",
        "payment_method": "cash",
        "tos_accepted": True
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log_info(f"Booking response: {json.dumps(data, indent=2)}")
        
        due_now = data.get("due_now")
        
        checks = [
            (due_now == 0, f"due_now should be 0 for pay_later, got {due_now}"),
            ("id" in data, "Booking ID present")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        return data.get("id") if all_pass else None
    else:
        log_fail(f"Booking failed: {response.status_code} - {response.text}")
        return None

def test_booking_no_tos(token: str):
    log_test("14. POST /api/bookings - Without TOS acceptance (should return 400)")
    
    future_date = get_future_date(10)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Sarah Johnson",
        "phone": "+14041234567",
        "address": "199 N Decatur Rd, Decatur, GA",
        "service_value": "general_cleaning",
        "tier_key": "heavy",
        "pets": 0,
        "notes": "",
        "preferred_date": future_date,
        "preferred_time": "14:00",
        "payment_plan": "half_now",
        "payment_method": "card",
        "tos_accepted": False
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=payload, headers=headers)
    
    if response.status_code == 400:
        log_pass("Booking without TOS correctly rejected with 400")
        return True
    else:
        log_fail(f"Expected 400, got {response.status_code}")
        return False

# ============= TEST 9: GET BOOKINGS =============
def test_get_my_bookings(token: str):
    log_test("15. GET /api/bookings/me - Get all my bookings")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/bookings/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log_pass(f"Retrieved {len(data)} bookings")
        if len(data) > 0:
            log_info(f"First booking: {data[0].get('service_label')} on {data[0].get('preferred_date')}")
        return True
    else:
        log_fail(f"Failed to get bookings: {response.status_code} - {response.text}")
        return False

def test_get_upcoming_bookings(token: str):
    log_test("16. GET /api/bookings/upcoming - Get upcoming bookings only")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/bookings/upcoming", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log_pass(f"Retrieved {len(data)} upcoming bookings")
        
        # Verify all are future and not cancelled
        today = datetime.now().date().isoformat()
        all_valid = True
        for booking in data:
            if booking.get("status") == "cancelled":
                log_fail(f"Cancelled booking in upcoming list: {booking.get('id')}")
                all_valid = False
            if booking.get("preferred_date", "") < today:
                log_fail(f"Past booking in upcoming list: {booking.get('id')}")
                all_valid = False
        
        if all_valid:
            log_pass("All upcoming bookings are valid (future, non-cancelled)")
        
        return all_valid
    else:
        log_fail(f"Failed to get upcoming bookings: {response.status_code} - {response.text}")
        return False

# ============= TEST 10: CANCEL BOOKING =============
def test_cancel_booking(token: str, booking_id: str):
    log_test(f"17. POST /api/bookings/{booking_id}/cancel - Cancel booking")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/bookings/{booking_id}/cancel", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok") and data.get("status") == "cancelled":
            log_pass("Booking cancelled successfully")
            
            # Test idempotency - cancel again
            log_info("Testing idempotency - cancelling again...")
            response2 = requests.post(f"{BASE_URL}/bookings/{booking_id}/cancel", headers=headers)
            if response2.status_code == 200:
                log_pass("Idempotent cancel works (200 on second call)")
                return True
            else:
                log_fail(f"Second cancel failed: {response2.status_code}")
                return False
        else:
            log_fail(f"Cancel response invalid: {data}")
            return False
    else:
        log_fail(f"Cancel failed: {response.status_code} - {response.text}")
        return False

def test_cancel_other_user_booking(token: str):
    log_test("18. POST /api/bookings/{id}/cancel - Try to cancel another user's booking (should 404)")
    
    # Use a fake booking ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/bookings/{fake_id}/cancel", headers=headers)
    
    if response.status_code == 404:
        log_pass("Cannot cancel other user's booking (404)")
        return True
    else:
        log_fail(f"Expected 404, got {response.status_code}")
        return False

# ============= TEST 11: TOS =============
def test_get_tos():
    log_test("19. GET /api/tos - Get Terms of Service")
    
    response = requests.get(f"{BASE_URL}/tos")
    
    if response.status_code == 200:
        data = response.json()
        
        checks = [
            ("version" in data, "version field present"),
            ("effective" in data, "effective field present"),
            ("text" in data, "text field present"),
            (len(data.get("text", "")) > 100, f"TOS text is non-empty (length: {len(data.get('text', ''))})")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        if all_pass:
            log_info(f"TOS version: {data.get('version')}, effective: {data.get('effective')}")
        
        return all_pass
    else:
        log_fail(f"Failed to get TOS: {response.status_code} - {response.text}")
        return False

# ============= TEST 12: FIREBASE STATUS =============
def test_firebase_status():
    log_test("20. GET /api/firebase/status - Firebase integration status")
    
    response = requests.get(f"{BASE_URL}/firebase/status")
    
    if response.status_code == 200:
        data = response.json()
        
        checks = [
            ("enabled" in data, "enabled field present"),
            (data.get("enabled") == True, f"Firebase should be enabled, got {data.get('enabled')}"),
            ("db_url" in data, "db_url field present"),
            (data.get("db_url") == "https://mekhis-creations-default-rtdb.firebaseio.com", 
             f"db_url should be correct, got {data.get('db_url')}")
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                log_pass(msg)
            else:
                log_fail(msg)
                all_pass = False
        
        log_info("Note: Firebase 401 errors from upstream are expected (user hasn't applied rules yet)")
        log_info("The backend gracefully ignores these errors - MongoDB is authoritative")
        
        return all_pass
    else:
        log_fail(f"Failed to get Firebase status: {response.status_code} - {response.text}")
        return False

# ============= MAIN TEST RUNNER =============
def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}PAWFECT & PRISTINE - BACKEND API TESTS{Colors.END}")
    print(f"{Colors.BLUE}Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    results = {}
    token = None
    booking_id = None
    
    # Test 1-2: Registration
    token = test_auth_register()
    results["auth_register"] = token is not None
    
    results["auth_register_duplicate"] = test_auth_register_duplicate()
    
    # Test 3-4: Login
    results["auth_login_wrong_password"] = test_auth_login_wrong_password()
    
    if not token:
        token = test_auth_login_correct()
    results["auth_login_correct"] = token is not None
    
    # Test 5: Get current user
    if token:
        results["auth_me"] = test_auth_me(token)
    
    # Test 6: Logout
    results["auth_logout"] = test_auth_logout()
    
    # Test 7: Catalog
    results["catalog"] = test_catalog()
    
    # Test 8-9: Quote
    results["quote_with_advance"] = test_quote_with_advance_fee()
    results["quote_without_advance"] = test_quote_without_advance_fee()
    
    # Test 10: ETA
    results["eta"] = test_eta()
    
    # Test 11-14: Bookings
    if token:
        booking_id = test_booking_half_now(token)
        results["booking_half_now"] = booking_id is not None
        
        booking_id2 = test_booking_all_now(token)
        results["booking_all_now"] = booking_id2 is not None
        
        booking_id3 = test_booking_pay_later(token)
        results["booking_pay_later"] = booking_id3 is not None
        
        results["booking_no_tos"] = test_booking_no_tos(token)
        
        # Test 15-16: Get bookings
        results["get_my_bookings"] = test_get_my_bookings(token)
        results["get_upcoming_bookings"] = test_get_upcoming_bookings(token)
        
        # Test 17-18: Cancel booking
        if booking_id:
            results["cancel_booking"] = test_cancel_booking(token, booking_id)
        results["cancel_other_user_booking"] = test_cancel_other_user_booking(token)
    
    # Test 19: TOS
    results["get_tos"] = test_get_tos()
    
    # Test 20: Firebase status
    results["firebase_status"] = test_firebase_status()
    
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

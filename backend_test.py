#!/usr/bin/env python3
"""
Backend API test suite for Pawfect & Pristine v1.7 - LocationIQ Integration
Re-testing geocoding with LocationIQ (no more Nominatim rate limits)

CRITICAL TESTS:
1-3: GET /api/geocode/suggest with various queries
4-5: POST /api/eta with in-area and out-of-area addresses
6-8: POST /api/bookings with various addresses (in-area, out-of-area, garbage)
9: Anonymous POST /api/bookings (expect 401)
10: Regression tests (catalog, login, paypal endpoints)
"""

import httpx
import asyncio
from datetime import datetime, timedelta
import random
import string

BASE_URL = "https://48511398-4d7d-4642-be1e-d796c8f83659.preview.emergentagent.com"
API_PREFIX = "/api"

# Test credentials
ADMIN_EMAIL = "admin@pawfectpristine.com"
ADMIN_PASSWORD = "Pawfect2026!"

# Test results tracking
test_results = []


def log_test(test_num, description, passed, status_code=None, detail=None):
    """Log test result"""
    result = "✅ PASS" if passed else "❌ FAIL"
    msg = f"Test {test_num}: {description} - {result}"
    if status_code:
        msg += f" (HTTP {status_code})"
    if detail:
        msg += f"\n    Detail: {detail[:200]}"
    print(msg)
    test_results.append({
        "test_num": test_num,
        "description": description,
        "passed": passed,
        "status_code": status_code,
        "detail": detail
    })


def generate_unique_email():
    """Generate unique email for test users"""
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{rand}@pawfecttest.com"


async def register_user(client, email, password="TestPass123!", name="Test User"):
    """Register a new user and return token"""
    response = await client.post(
        f"{BASE_URL}{API_PREFIX}/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "phone": "4701234567",
            "marketing_opt_in": True
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    return None


async def get_future_date(days_out=9):
    """Get a future date string"""
    future = datetime.now() + timedelta(days=days_out)
    return future.strftime("%Y-%m-%d")


async def get_unique_future_date():
    """Get a unique future date to avoid conflicts - use current timestamp"""
    import time
    # Use days based on current timestamp to ensure uniqueness
    days_out = 10 + (int(time.time()) % 20)  # Between 10-30 days out
    future = datetime.now() + timedelta(days=days_out)
    return future.strftime("%Y-%m-%d")


async def run_tests():
    """Run all backend tests"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\n" + "="*80)
        print("CRITICAL TESTS — LocationIQ Geocoding")
        print("="*80 + "\n")
        
        # TEST 1: GET /api/geocode/suggest?q=199+N+Decatur
        print("Test 1: GET /api/geocode/suggest?q=199+N+Decatur...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/geocode/suggest?q=199+N+Decatur")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if len(results) >= 1:
                first_result = results[0]
                label = first_result.get("label", "")
                has_georgia = "georgia" in label.lower() or "ga" in label.lower() or "decatur" in label.lower()
                has_label = "label" in first_result
                has_address = "address" in first_result
                has_lat = "lat" in first_result
                has_lon = "lon" in first_result
                has_state = "state" in first_result
                
                if has_georgia and has_label and has_address and has_lat and has_lon and has_state:
                    log_test(1, "GET /api/geocode/suggest?q=199+N+Decatur returns GA result with all fields", True, 200, 
                            f"label='{label}', lat={first_result.get('lat')}, lon={first_result.get('lon')}, state={first_result.get('state')}")
                else:
                    log_test(1, "GET /api/geocode/suggest?q=199+N+Decatur missing fields or not in GA", False, 200, 
                            f"has_georgia={has_georgia}, has_label={has_label}, has_address={has_address}, has_lat={has_lat}, has_lon={has_lon}, has_state={has_state}, label='{label}'")
            else:
                log_test(1, "GET /api/geocode/suggest?q=199+N+Decatur returns empty results (FAIL - LocationIQ should work)", False, 200, 
                        f"results count={len(results)}")
        else:
            log_test(1, "GET /api/geocode/suggest?q=199+N+Decatur should return 200", False, response.status_code, response.text[:200])
        
        # TEST 2: GET /api/geocode/suggest?q=1280+W+Peachtree+Atlanta
        print("\nTest 2: GET /api/geocode/suggest?q=1280+W+Peachtree+Atlanta...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/geocode/suggest?q=1280+W+Peachtree+Atlanta")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if len(results) >= 1:
                first_result = results[0]
                label = first_result.get("label", "")
                has_georgia = "georgia" in label.lower() or "ga" in label.lower() or "atlanta" in label.lower()
                
                if has_georgia:
                    log_test(2, "GET /api/geocode/suggest?q=1280+W+Peachtree+Atlanta returns GA result", True, 200, 
                            f"label='{label}', lat={first_result.get('lat')}, lon={first_result.get('lon')}")
                else:
                    log_test(2, "GET /api/geocode/suggest?q=1280+W+Peachtree+Atlanta not in GA", False, 200, 
                            f"label='{label}'")
            else:
                log_test(2, "GET /api/geocode/suggest?q=1280+W+Peachtree+Atlanta returns empty results (FAIL - LocationIQ should work)", False, 200, 
                        f"results count={len(results)}")
        else:
            log_test(2, "GET /api/geocode/suggest?q=1280+W+Peachtree+Atlanta should return 200", False, response.status_code, response.text[:200])
        
        # TEST 3: GET /api/geocode/suggest?q=ab (too short)
        print("\nTest 3: GET /api/geocode/suggest?q=ab (too short, < 3 chars)...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/geocode/suggest?q=ab")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if isinstance(results, list) and len(results) == 0:
                log_test(3, "GET /api/geocode/suggest?q=ab returns empty results", True, 200, 
                        f"results={results}")
            else:
                log_test(3, "GET /api/geocode/suggest?q=ab should return empty results", False, 200, 
                        f"results count={len(results)}")
        else:
            log_test(3, "GET /api/geocode/suggest?q=ab should return 200", False, response.status_code, response.text[:200])
        
        # TEST 4: POST /api/eta with in-area address
        print("\nTest 4: POST /api/eta with '199 North Candler Street, Decatur, Georgia, 30030'...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/eta",
            json={"address": "199 North Candler Street, Decatur, Georgia, 30030"}
        )
        
        if response.status_code == 200:
            data = response.json()
            zone = data.get("zone")
            extra_fee = data.get("extra_fee")
            distance_miles = data.get("distance_miles")
            
            if zone == "standard" and extra_fee == 0 and distance_miles is not None and distance_miles < 5:
                log_test(4, "POST /api/eta with in-area address returns zone=standard, extra_fee=0, distance<5mi", True, 200, 
                        f"zone={zone}, extra_fee={extra_fee}, distance_miles={distance_miles}")
            else:
                log_test(4, "POST /api/eta with in-area address has wrong values", False, 200, 
                        f"zone={zone} (expected 'standard'), extra_fee={extra_fee} (expected 0), distance_miles={distance_miles} (expected <5)")
        else:
            log_test(4, "POST /api/eta with in-area address should return 200", False, response.status_code, response.text[:200])
        
        # TEST 5: POST /api/eta with out-of-area address
        print("\nTest 5: POST /api/eta with 'Times Square, New York, NY'...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/eta",
            json={"address": "Times Square, New York, NY"}
        )
        
        if response.status_code == 200:
            data = response.json()
            zone = data.get("zone")
            distance_miles = data.get("distance_miles")
            
            if zone == "out_of_range" and distance_miles is not None and distance_miles > 500:
                log_test(5, "POST /api/eta with out-of-area address returns zone=out_of_range, distance>500mi", True, 200, 
                        f"zone={zone}, distance_miles={distance_miles}")
            else:
                log_test(5, "POST /api/eta with out-of-area address has wrong values", False, 200, 
                        f"zone={zone} (expected 'out_of_range'), distance_miles={distance_miles} (expected >500)")
        else:
            log_test(5, "POST /api/eta with out-of-area address should return 200", False, response.status_code, response.text[:200])
        
        print("\n" + "="*80)
        print("CRITICAL TESTS — Booking with Address Validation")
        print("="*80 + "\n")
        
        # Register a fresh user for booking tests
        test_email = generate_unique_email()
        token = await register_user(client, test_email, name="Booking Tester")
        
        if not token:
            print("⚠ Could not register user for booking tests, skipping tests 6-8")
            log_test(6, "POST /api/bookings with in-area address (user registration failed)", False, None, "Could not register test user")
            log_test(7, "POST /api/bookings with out-of-area address (user registration failed)", False, None, "Could not register test user")
            log_test(8, "POST /api/bookings with garbage address (user registration failed)", False, None, "Could not register test user")
        else:
            future_date = await get_unique_future_date()  # Use unique date to avoid conflicts
            
            # TEST 6: POST /api/bookings with in-area address
            print("Test 6: POST /api/bookings (authed) with in-area address...")
            # Use a unique time to avoid conflicts
            import random
            time_options = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]
            random_time = random.choice(time_options)
            
            booking_payload = {
                "name": "Booking Tester",
                "phone": "4701234567",
                "address": "199 North Candler Street, Decatur, Georgia, 30030",
                "service_value": "general_cleaning",
                "tier_key": "standard",
                "preferred_date": future_date,
                "preferred_time": random_time,
                "payment_plan": "pay_later",
                "payment_method": "cash",
                "tos_accepted": True,
                "access_method": "home"
            }
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=booking_payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                booking_id = data.get("id")
                eta = data.get("eta", {})
                eta_zone = eta.get("zone")
                
                if booking_id and eta_zone == "standard":
                    log_test(6, "POST /api/bookings with in-area address returns 200 with booking_id and eta.zone=standard", True, 200, 
                            f"booking_id={booking_id}, eta.zone={eta_zone}, grand_total={data.get('grand_total')}")
                else:
                    log_test(6, "POST /api/bookings with in-area address missing fields or wrong zone", False, 200, 
                            f"booking_id={booking_id}, eta.zone={eta_zone} (expected 'standard')")
            else:
                log_test(6, "POST /api/bookings with in-area address should return 200", False, response.status_code, response.text[:200])
            
            # TEST 7: POST /api/bookings with out-of-area address
            print("\nTest 7: POST /api/bookings (authed) with out-of-area address...")
            out_of_area_payload = booking_payload.copy()
            out_of_area_payload["address"] = "Times Square, New York, NY"
            # Use a different random time to avoid conflicts
            out_of_area_payload["preferred_time"] = random.choice([t for t in time_options if t != random_time])
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=out_of_area_payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 400:
                data = response.json()
                detail = data.get("detail", "")
                has_service_area_msg = "outside our service area" in detail.lower()
                has_phone = "(470) 381-4682" in detail
                
                if has_service_area_msg and has_phone:
                    log_test(7, "POST /api/bookings with out-of-area address returns 400 with correct message", True, 400, detail)
                else:
                    log_test(7, "POST /api/bookings with out-of-area address returns 400 but missing required text", False, 400, 
                            f"has_service_area_msg={has_service_area_msg}, has_phone={has_phone}, detail='{detail}'")
            else:
                log_test(7, "POST /api/bookings with out-of-area address should return 400", False, response.status_code, response.text[:200])
            
            # TEST 8: POST /api/bookings with garbage address
            print("\nTest 8: POST /api/bookings (authed) with garbage address...")
            garbage_payload = booking_payload.copy()
            garbage_payload["address"] = "asdfqwerzxcvb 99999 garbage"
            # Use a different random time to avoid conflicts
            garbage_payload["preferred_time"] = random.choice([t for t in time_options if t not in [random_time, out_of_area_payload["preferred_time"]]])
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=garbage_payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 400:
                data = response.json()
                detail = data.get("detail", "")
                has_address_msg = "couldn't find that address" in detail.lower() or "outside our service area" in detail.lower()
                
                if has_address_msg:
                    log_test(8, "POST /api/bookings with garbage address returns 400 with correct message", True, 400, detail)
                else:
                    log_test(8, "POST /api/bookings with garbage address returns 400 but unclear message", False, 400, 
                            f"detail='{detail}'")
            else:
                log_test(8, "POST /api/bookings with garbage address should return 400", False, response.status_code, response.text[:200])
        
        # TEST 9: Anonymous POST /api/bookings (NO Authorization header)
        print("\nTest 9: Anonymous POST /api/bookings (NO Authorization header)...")
        # Use a unique time far in the future to avoid conflicts
        future_date_anon = await get_future_date(15)
        anon_payload = {
            "name": "Anonymous User",
            "phone": "4701234567",
            "address": "199 North Candler Street, Decatur, Georgia, 30030",
            "service_value": "general_cleaning",
            "tier_key": "standard",
            "preferred_date": future_date_anon,
            "preferred_time": "09:00",
            "payment_plan": "pay_later",
            "payment_method": "cash",
            "tos_accepted": True,
            "access_method": "home"
        }
        
        # Create a NEW client without cookies to test anonymous access
        async with httpx.AsyncClient(timeout=30.0) as anon_client:
            response = await anon_client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=anon_payload
            )
        
        if response.status_code == 401:
            log_test(9, "Anonymous POST /api/bookings returns 401", True, 401, response.json().get("detail", ""))
        else:
            log_test(9, "Anonymous POST /api/bookings should return 401", False, response.status_code, response.text[:200])
        
        print("\n" + "="*80)
        print("REGRESSION — Quick Spot-Check")
        print("="*80 + "\n")
        
        # TEST 10a: GET /api/catalog
        print("Test 10a: GET /api/catalog...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/catalog")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and len(data) > 0:
                log_test("10a", "GET /api/catalog returns 200", True, 200, f"services count={len(data)}")
            else:
                log_test("10a", "GET /api/catalog returns 200 but empty or wrong format", False, 200, f"data type={type(data)}")
        else:
            log_test("10a", "GET /api/catalog should return 200", False, response.status_code, response.text[:200])
        
        # TEST 10b: POST /api/auth/login
        print("\nTest 10b: POST /api/auth/login (admin@pawfectpristine.com / Pawfect2026!)...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "user" in data and "token" in data:
                log_test("10b", "POST /api/auth/login returns 200", True, 200, f"email={ADMIN_EMAIL}")
            else:
                log_test("10b", "POST /api/auth/login returns 200 but missing fields", False, 200, f"data keys={list(data.keys())}")
        else:
            log_test("10b", "POST /api/auth/login should return 200", False, response.status_code, response.text[:200])
        
        # TEST 10c: POST /api/paypal/create-order
        print("\nTest 10c: POST /api/paypal/create-order with amount=1.00...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/paypal/create-order",
            json={"amount": 1.00, "currency": "USD"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                log_test("10c", "POST /api/paypal/create-order returns 200", True, 200, f"order_id={data['id']}")
            else:
                log_test("10c", "POST /api/paypal/create-order returns 200 but missing id", False, 200, f"data={data}")
        else:
            log_test("10c", "POST /api/paypal/create-order should return 200", False, response.status_code, response.text[:200])
        
        # TEST 10d: GET /api/paypal/config
        print("\nTest 10d: GET /api/paypal/config...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/paypal/config")
        
        if response.status_code == 200:
            data = response.json()
            if "enabled" in data and "client_id" in data:
                log_test("10d", "GET /api/paypal/config returns 200", True, 200, f"enabled={data.get('enabled')}, env={data.get('env')}")
            else:
                log_test("10d", "GET /api/paypal/config returns 200 but missing fields", False, 200, f"data keys={list(data.keys())}")
        else:
            log_test("10d", "GET /api/paypal/config should return 200", False, response.status_code, response.text[:200])


async def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("PAWFECT & PRISTINE v1.7 BACKEND TEST SUITE")
    print("LocationIQ Geocoding Integration")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Prefix: {API_PREFIX}")
    print(f"Test Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print("="*80 + "\n")
    
    await run_tests()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    if failed > 0:
        print("FAILED TESTS:")
        for r in test_results:
            if not r["passed"]:
                print(f"  ❌ Test {r['test_num']}: {r['description']}")
                if r["detail"]:
                    print(f"     Detail: {r['detail'][:200]}")
        print()
    
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

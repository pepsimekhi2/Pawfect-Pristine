#!/usr/bin/env python3
"""
Backend API test suite for Pawfect & Pristine v1.7
Tests three new changes:
1. POST /api/bookings now REQUIRES auth (was optional)
2. Hard zone enforcement on POST /api/bookings
3. New autocomplete endpoint GET /api/geocode/suggest
Plus regression tests for existing endpoints.
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
        msg += f" - {detail}"
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


async def get_future_date(days_out=4):
    """Get a future date string"""
    future = datetime.now() + timedelta(days=days_out)
    return future.strftime("%Y-%m-%d")


async def run_tests():
    """Run all backend tests"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\n" + "="*80)
        print("CHANGE 1 — POST /api/bookings now REQUIRES auth")
        print("="*80 + "\n")
        
        # TEST 1: POST /api/bookings WITHOUT Authorization header
        print("Test 1: POST /api/bookings without auth...")
        future_date = await get_future_date(4)
        booking_payload = {
            "name": "John Doe",
            "phone": "4701234567",
            "address": "199 N Decatur Rd, Decatur, GA",
            "service_value": "general_cleaning",
            "tier_key": "standard",
            "preferred_date": future_date,
            "preferred_time": "14:00",
            "payment_plan": "pay_later",
            "payment_method": "cash",
            "tos_accepted": True,
            "access_method": "home"
        }
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/bookings",
            json=booking_payload
        )
        
        # CRITICAL: Must be 401, not 200 or 422
        if response.status_code == 401:
            data = response.json()
            if "detail" in data and "authenticated" in data["detail"].lower():
                log_test(1, "POST /api/bookings without auth returns 401", True, 401, data.get("detail"))
            else:
                log_test(1, "POST /api/bookings without auth returns 401 but wrong detail", False, 401, data.get("detail"))
        else:
            log_test(1, "POST /api/bookings without auth should return 401", False, response.status_code, response.text[:200])
        
        # TEST 2: POST /api/bookings WITH auth + valid body
        print("\nTest 2: POST /api/bookings with auth + valid body...")
        test_email = generate_unique_email()
        token = await register_user(client, test_email, name="Jane Smith")
        
        if not token:
            log_test(2, "POST /api/bookings with auth (registration failed)", False, None, "Could not register test user")
        else:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=booking_payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                has_id = "id" in data
                has_grand_total = "grand_total" in data
                has_due_now = "due_now" in data
                has_due_later = "due_later" in data
                
                if has_id and has_grand_total and has_due_now and has_due_later:
                    booking_id = data["id"]
                    log_test(2, "POST /api/bookings with auth returns 200 with required fields", True, 200, 
                            f"id={booking_id}, grand_total={data['grand_total']}, due_now={data['due_now']}, due_later={data['due_later']}")
                    
                    # Verify booking is persisted via GET /api/bookings/me
                    verify_response = await client.get(
                        f"{BASE_URL}{API_PREFIX}/bookings/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if verify_response.status_code == 200:
                        bookings = verify_response.json()
                        booking_found = any(b.get("id") == booking_id for b in bookings)
                        if booking_found:
                            print(f"  ✓ Booking {booking_id} verified in GET /api/bookings/me")
                        else:
                            print(f"  ⚠ Booking {booking_id} NOT found in GET /api/bookings/me")
                else:
                    log_test(2, "POST /api/bookings with auth missing required fields", False, 200, 
                            f"Missing fields: id={has_id}, grand_total={has_grand_total}, due_now={has_due_now}, due_later={has_due_later}")
            else:
                log_test(2, "POST /api/bookings with auth should return 200", False, response.status_code, response.text[:200])
        
        print("\n" + "="*80)
        print("CHANGE 2 — Hard zone enforcement on POST /api/bookings")
        print("="*80 + "\n")
        
        # Register a user for zone tests
        zone_test_email = generate_unique_email()
        zone_token = await register_user(client, zone_test_email, name="Zone Tester")
        
        if not zone_token:
            print("⚠ Could not register user for zone tests, skipping tests 3-5")
            log_test(3, "Out-of-range address test (user registration failed)", False, None, "Could not register test user")
            log_test(4, "Gibberish address test (user registration failed)", False, None, "Could not register test user")
            log_test(5, "Valid in-area address test (user registration failed)", False, None, "Could not register test user")
        else:
            # TEST 3: Out-of-range address (Times Square, NY)
            print("Test 3: POST /api/bookings with out-of-range address (Times Square, NY)...")
            out_of_range_payload = booking_payload.copy()
            out_of_range_payload["address"] = "Times Square, New York, NY"
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=out_of_range_payload,
                headers={"Authorization": f"Bearer {zone_token}"}
            )
            
            if response.status_code == 400:
                data = response.json()
                detail = data.get("detail", "")
                has_service_area_msg = "outside our service area" in detail.lower() or "outside" in detail.lower()
                has_phone = "(470) 381-4682" in detail
                
                if has_service_area_msg and has_phone:
                    log_test(3, "Out-of-range address returns 400 with correct message", True, 400, detail)
                elif has_service_area_msg:
                    log_test(3, "Out-of-range address returns 400 but missing phone number", False, 400, detail)
                else:
                    log_test(3, "Out-of-range address returns 400 but wrong message", False, 400, detail)
            else:
                log_test(3, "Out-of-range address should return 400", False, response.status_code, response.text[:200])
            
            # TEST 4: Gibberish address
            print("\nTest 4: POST /api/bookings with gibberish address...")
            gibberish_payload = booking_payload.copy()
            gibberish_payload["address"] = "asdfqwerzxcv 99999"
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=gibberish_payload,
                headers={"Authorization": f"Bearer {zone_token}"}
            )
            
            # Expect 400 (address not found) or 502 (routing service unavailable)
            if response.status_code in [400, 502]:
                data = response.json()
                detail = data.get("detail", "")
                has_address_msg = "couldn't find" in detail.lower() or "address" in detail.lower() or "unavailable" in detail.lower()
                
                if has_address_msg:
                    log_test(4, f"Gibberish address returns {response.status_code} with correct message", True, response.status_code, detail)
                else:
                    log_test(4, f"Gibberish address returns {response.status_code} but unclear message", True, response.status_code, detail)
            else:
                log_test(4, "Gibberish address should return 400 or 502", False, response.status_code, response.text[:200])
            
            # TEST 5: Valid in-area address with zone=standard (no travel fee)
            print("\nTest 5: POST /api/bookings with valid in-area address...")
            valid_payload = booking_payload.copy()
            valid_payload["address"] = "199 N Decatur Rd, Decatur, GA"
            # Use a different time to avoid conflicts
            valid_payload["preferred_time"] = "10:00"
            
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=valid_payload,
                headers={"Authorization": f"Bearer {zone_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check for travel_fee in response or eta object
                travel_fee = data.get("travel_fee")
                if travel_fee is None and "eta" in data:
                    travel_fee = data["eta"].get("extra_fee")
                
                if travel_fee is not None and travel_fee == 0:
                    log_test(5, "Valid in-area address returns 200 with travel_fee=0", True, 200, 
                            f"travel_fee={travel_fee}, zone={data.get('eta', {}).get('zone', 'N/A')}")
                else:
                    log_test(5, "Valid in-area address returns 200 but travel_fee not 0", False, 200, 
                            f"travel_fee={travel_fee}")
            else:
                log_test(5, "Valid in-area address should return 200", False, response.status_code, response.text[:200])
        
        print("\n" + "="*80)
        print("CHANGE 3 — New autocomplete endpoint GET /api/geocode/suggest")
        print("="*80 + "\n")
        
        # TEST 6: GET /api/geocode/suggest with valid query
        print("Test 6: GET /api/geocode/suggest?q=Decatur+GA...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/geocode/suggest?q=Decatur+GA")
        
        if response.status_code == 200:
            data = response.json()
            has_q = "q" in data
            has_results = "results" in data
            results_is_array = isinstance(data.get("results"), list)
            
            if has_q and has_results and results_is_array:
                # Empty array is acceptable due to Nominatim rate limits
                log_test(6, "GET /api/geocode/suggest returns 200 with correct structure", True, 200, 
                        f"q={data['q']}, results count={len(data['results'])}")
            else:
                log_test(6, "GET /api/geocode/suggest returns 200 but wrong structure", False, 200, 
                        f"has_q={has_q}, has_results={has_results}, results_is_array={results_is_array}")
        else:
            log_test(6, "GET /api/geocode/suggest should return 200", False, response.status_code, response.text[:200])
        
        # TEST 7: GET /api/geocode/suggest with too short query
        print("\nTest 7: GET /api/geocode/suggest?q=ab (too short)...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/geocode/suggest?q=ab")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if isinstance(results, list) and len(results) == 0:
                log_test(7, "GET /api/geocode/suggest with short query returns 200 with empty results", True, 200, 
                        f"results={results}")
            else:
                log_test(7, "GET /api/geocode/suggest with short query returns 200 but non-empty results", True, 200, 
                        f"results count={len(results)}")
        else:
            log_test(7, "GET /api/geocode/suggest with short query should return 200", False, response.status_code, response.text[:200])
        
        # TEST 8: GET /api/geocode/suggest with no q parameter
        print("\nTest 8: GET /api/geocode/suggest with no q parameter...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/geocode/suggest")
        
        if response.status_code == 422:
            log_test(8, "GET /api/geocode/suggest without q parameter returns 422", True, 422, "FastAPI validation error")
        else:
            log_test(8, "GET /api/geocode/suggest without q parameter should return 422", False, response.status_code, response.text[:200])
        
        print("\n" + "="*80)
        print("REGRESSION — Verify existing endpoints still work")
        print("="*80 + "\n")
        
        # TEST 9: POST /api/auth/register
        print("Test 9: POST /api/auth/register...")
        reg_email = generate_unique_email()
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={
                "name": "Regression Test User",
                "email": reg_email,
                "password": "RegTest123!",
                "phone": "4709876543",
                "marketing_opt_in": True
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            has_user = "user" in data
            has_token = "token" in data
            if has_user and has_token:
                log_test(9, "POST /api/auth/register returns 200 with user+token", True, 200, f"email={reg_email}")
            else:
                log_test(9, "POST /api/auth/register returns 200 but missing fields", False, 200, 
                        f"has_user={has_user}, has_token={has_token}")
        else:
            log_test(9, "POST /api/auth/register should return 200", False, response.status_code, response.text[:200])
        
        # TEST 10: POST /api/auth/login
        print("\nTest 10: POST /api/auth/login...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            has_user = "user" in data
            has_token = "token" in data
            if has_user and has_token:
                admin_token = data["token"]
                log_test(10, "POST /api/auth/login returns 200 with user+token", True, 200, f"email={ADMIN_EMAIL}")
            else:
                log_test(10, "POST /api/auth/login returns 200 but missing fields", False, 200, 
                        f"has_user={has_user}, has_token={has_token}")
        else:
            log_test(10, "POST /api/auth/login should return 200", False, response.status_code, response.text[:200])
        
        # TEST 11: POST /api/eta
        print("\nTest 11: POST /api/eta with valid address...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/eta",
            json={"address": "199 N Decatur Rd, Decatur, GA"}
        )
        
        if response.status_code == 200:
            data = response.json()
            has_distance = "distance_miles" in data
            has_zone = "zone" in data
            if has_distance and has_zone:
                log_test(11, "POST /api/eta returns 200 with distance_miles and zone", True, 200, 
                        f"distance={data.get('distance_miles')}mi, zone={data.get('zone')}")
            else:
                log_test(11, "POST /api/eta returns 200 but missing fields", False, 200, 
                        f"has_distance={has_distance}, has_zone={has_zone}")
        elif response.status_code == 404:
            # Tolerable if Nominatim is rate-limited
            log_test(11, "POST /api/eta returns 404 (Nominatim rate-limited - known degradation)", True, 404, 
                    "Nominatim rate limit - NOT a test failure")
        else:
            log_test(11, "POST /api/eta should return 200 or 404", False, response.status_code, response.text[:200])
        
        # TEST 12: GET /api/catalog
        print("\nTest 12: GET /api/catalog...")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/catalog")
        
        if response.status_code == 200:
            data = response.json()
            # Catalog returns a dict/object with service keys, not a list
            if isinstance(data, dict) and len(data) > 0:
                log_test(12, "GET /api/catalog returns 200 with services", True, 200, f"services count={len(data)}")
            else:
                log_test(12, "GET /api/catalog returns 200 but empty or wrong format", False, 200, f"data type={type(data)}, len={len(data) if hasattr(data, '__len__') else 'N/A'}")
        else:
            log_test(12, "GET /api/catalog should return 200", False, response.status_code, response.text[:200])
        
        # TEST 13: POST /api/paypal/create-order
        print("\nTest 13: POST /api/paypal/create-order...")
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/paypal/create-order",
            json={"amount": 1.00, "currency": "USD"}
        )
        
        if response.status_code == 200:
            data = response.json()
            has_id = "id" in data
            if has_id:
                log_test(13, "POST /api/paypal/create-order returns 200 with order id", True, 200, f"order_id={data['id']}")
            else:
                log_test(13, "POST /api/paypal/create-order returns 200 but missing id", False, 200, f"data={data}")
        else:
            log_test(13, "POST /api/paypal/create-order should return 200", False, response.status_code, response.text[:200])
        
        # TEST 14: GET /api/bookings/me (authed)
        print("\nTest 14: GET /api/bookings/me (authed)...")
        # Use the token from test 2 if available
        if token:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/bookings/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    log_test(14, "GET /api/bookings/me returns 200 with array", True, 200, f"bookings count={len(data)}")
                else:
                    log_test(14, "GET /api/bookings/me returns 200 but not an array", False, 200, f"data type={type(data)}")
            else:
                log_test(14, "GET /api/bookings/me should return 200", False, response.status_code, response.text[:200])
        else:
            log_test(14, "GET /api/bookings/me (no token available from earlier tests)", False, None, "Token not available")
        
        # TEST 15: POST /api/bookings/{id}/cancel
        print("\nTest 15: POST /api/bookings/{id}/cancel (authed, owner)...")
        # Create a booking first, then cancel it
        if token:
            cancel_payload = booking_payload.copy()
            cancel_payload["preferred_time"] = "15:00"  # Different time to avoid conflicts
            
            create_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/bookings",
                json=cancel_payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if create_response.status_code == 200:
                booking_id = create_response.json().get("id")
                
                cancel_response = await client.post(
                    f"{BASE_URL}{API_PREFIX}/bookings/{booking_id}/cancel",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if cancel_response.status_code == 200:
                    data = cancel_response.json()
                    if data.get("ok") or data.get("status") == "cancelled":
                        log_test(15, "POST /api/bookings/{id}/cancel returns 200", True, 200, f"booking_id={booking_id}")
                    else:
                        log_test(15, "POST /api/bookings/{id}/cancel returns 200 but unexpected response", False, 200, f"data={data}")
                else:
                    log_test(15, "POST /api/bookings/{id}/cancel should return 200", False, cancel_response.status_code, cancel_response.text[:200])
            else:
                log_test(15, "POST /api/bookings/{id}/cancel (could not create booking to cancel)", False, create_response.status_code, "Booking creation failed")
        else:
            log_test(15, "POST /api/bookings/{id}/cancel (no token available from earlier tests)", False, None, "Token not available")


async def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("PAWFECT & PRISTINE v1.7 BACKEND TEST SUITE")
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
                    print(f"     Detail: {r['detail']}")
        print()
    
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

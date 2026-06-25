#!/usr/bin/env python3
"""
Backend API verification test for Vercel rewrite fix.
Tests all endpoints at the external URL that Vercel will proxy to.
"""

import requests
import json
import random
import string
from datetime import datetime, timedelta

# Base URL - the external URL that Vercel rewrites will proxy to
BASE_URL = "https://48511398-4d7d-4642-be1e-d796c8f83659.preview.emergentagent.com"

def random_email():
    """Generate a random email for testing"""
    rand = ''.join(random.choices(string.digits, k=6))
    return f"vercel-test-{rand}@example.com"

def print_test(test_name, passed, details=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {details}")
    if not passed:
        print()

def test_auth_register():
    """Test 1: POST /api/auth/register - CRITICAL (was returning 405)"""
    print("\n=== TEST 1: POST /api/auth/register ===")
    
    email = random_email()
    payload = {
        "name": "Vercel Test User",
        "email": email,
        "password": "TestPass123!",
        "marketing_opt_in": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=10)
        
        # Check for 405 error (CRITICAL - this was the user's issue)
        if response.status_code == 405:
            print_test("Register endpoint", False, f"CRITICAL: Got 405 Method Not Allowed - Vercel rewrite is broken!")
            return None, None
        
        # Check for success
        if response.status_code == 200:
            data = response.json()
            if "user" in data and "token" in data:
                print_test("Register returns 200 with user+token", True, f"Email: {email}")
                return email, data["token"]
            else:
                print_test("Register response structure", False, f"Missing user or token in response: {data}")
                return None, None
        else:
            print_test("Register endpoint", False, f"Status: {response.status_code}, Body: {response.text[:200]}")
            return None, None
            
    except Exception as e:
        print_test("Register endpoint", False, f"Exception: {str(e)}")
        return None, None

def test_auth_login(email, password="TestPass123!"):
    """Test 2: POST /api/auth/login"""
    print("\n=== TEST 2: POST /api/auth/login ===")
    
    if not email:
        print_test("Login test skipped", False, "No email from registration")
        return None
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload, timeout=10)
        
        if response.status_code == 405:
            print_test("Login endpoint", False, f"CRITICAL: Got 405 Method Not Allowed")
            return None
        
        if response.status_code == 200:
            data = response.json()
            if "user" in data and "token" in data:
                print_test("Login returns 200 with user+token", True)
                return data["token"]
            else:
                print_test("Login response structure", False, f"Missing user or token")
                return None
        else:
            print_test("Login endpoint", False, f"Status: {response.status_code}, Body: {response.text[:200]}")
            return None
            
    except Exception as e:
        print_test("Login endpoint", False, f"Exception: {str(e)}")
        return None

def test_quote_valid():
    """Test 3: POST /api/quote with valid data - CRITICAL (was returning 405)"""
    print("\n=== TEST 3: POST /api/quote (valid data) ===")
    
    payload = {
        "service_value": "general_cleaning",
        "tier_key": "standard"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/quote", json=payload, timeout=10)
        
        if response.status_code == 405:
            print_test("Quote endpoint", False, f"CRITICAL: Got 405 Method Not Allowed - Vercel rewrite is broken!")
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["total", "base_price", "service_label", "tier_label"]
            if all(field in data for field in required_fields):
                print_test("Quote returns 200 with required fields", True, f"Total: ${data.get('total')}")
                return True
            else:
                print_test("Quote response structure", False, f"Missing required fields: {data}")
                return False
        else:
            print_test("Quote endpoint", False, f"Status: {response.status_code}, Body: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_test("Quote endpoint", False, f"Exception: {str(e)}")
        return False

def test_quote_invalid():
    """Test 4: POST /api/quote with missing body - should return 422, NOT 405"""
    print("\n=== TEST 4: POST /api/quote (missing body) ===")
    
    payload = {}
    
    try:
        response = requests.post(f"{BASE_URL}/api/quote", json=payload, timeout=10)
        
        if response.status_code == 405:
            print_test("Quote validation", False, f"CRITICAL: Got 405 instead of 422 for invalid data")
            return False
        
        if response.status_code == 422:
            print_test("Quote returns 422 for invalid data (NOT 405)", True)
            return True
        else:
            print_test("Quote validation", False, f"Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Quote validation", False, f"Exception: {str(e)}")
        return False

def test_catalog():
    """Test 5: GET /api/catalog"""
    print("\n=== TEST 5: GET /api/catalog ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/catalog", timeout=10)
        
        if response.status_code == 405:
            print_test("Catalog endpoint", False, f"Got 405 Method Not Allowed")
            return False
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and len(data) > 0:
                print_test("Catalog returns 200 with data", True, f"Services: {len(data)}")
                return True
            else:
                print_test("Catalog response", False, f"Empty or invalid catalog: {data}")
                return False
        else:
            print_test("Catalog endpoint", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Catalog endpoint", False, f"Exception: {str(e)}")
        return False

def test_eta():
    """Test 6: POST /api/eta"""
    print("\n=== TEST 6: POST /api/eta ===")
    
    payload = {
        "address": "199 N Decatur Rd, Decatur, GA"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/eta", json=payload, timeout=10)
        
        if response.status_code == 405:
            print_test("ETA endpoint", False, f"Got 405 Method Not Allowed")
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "distance_miles" in data and "zone" in data:
                print_test("ETA returns 200 with distance+zone", True, f"Distance: {data.get('distance_miles')} miles")
                return True
            else:
                print_test("ETA response", False, f"Missing required fields: {data}")
                return False
        else:
            print_test("ETA endpoint", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("ETA endpoint", False, f"Exception: {str(e)}")
        return False

def test_paypal_create_order():
    """Test 7: POST /api/paypal/create-order"""
    print("\n=== TEST 7: POST /api/paypal/create-order ===")
    
    payload = {
        "amount": 1.00,
        "currency": "USD"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/paypal/create-order", json=payload, timeout=10)
        
        if response.status_code == 405:
            print_test("PayPal create-order", False, f"Got 405 Method Not Allowed")
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "status" in data:
                print_test("PayPal create-order returns 200 with id+status", True, f"Order ID: {data.get('id')}")
                return True
            else:
                print_test("PayPal create-order response", False, f"Missing id or status: {data}")
                return False
        else:
            print_test("PayPal create-order", False, f"Status: {response.status_code}, Body: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_test("PayPal create-order", False, f"Exception: {str(e)}")
        return False

def test_catalog_json():
    """Test 8: GET /catalog.json (static fallback)"""
    print("\n=== TEST 8: GET /catalog.json (static fallback) ===")
    
    try:
        response = requests.get(f"{BASE_URL}/catalog.json", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "general_cleaning" in data:
                print_test("Static catalog.json returns 200 with general_cleaning", True, f"Services: {len(data)}")
                return True
            else:
                print_test("Static catalog.json content", False, f"Missing general_cleaning: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                return False
        else:
            print_test("Static catalog.json", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Static catalog.json", False, f"Exception: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 80)
    print("BACKEND API VERIFICATION TEST")
    print("Testing external URL for Vercel rewrite fix")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)
    
    results = []
    
    # Test 1: Register (CRITICAL - was returning 405)
    email, token = test_auth_register()
    results.append(("POST /api/auth/register", email is not None and token is not None))
    
    # Test 2: Login
    login_token = test_auth_login(email) if email else None
    results.append(("POST /api/auth/login", login_token is not None))
    
    # Test 3: Quote with valid data (CRITICAL - was returning 405)
    quote_valid = test_quote_valid()
    results.append(("POST /api/quote (valid)", quote_valid))
    
    # Test 4: Quote with invalid data (should return 422, NOT 405)
    quote_invalid = test_quote_invalid()
    results.append(("POST /api/quote (invalid)", quote_invalid))
    
    # Test 5: Catalog
    catalog = test_catalog()
    results.append(("GET /api/catalog", catalog))
    
    # Test 6: ETA
    eta = test_eta()
    results.append(("POST /api/eta", eta))
    
    # Test 7: PayPal create-order
    paypal = test_paypal_create_order()
    results.append(("POST /api/paypal/create-order", paypal))
    
    # Test 8: Static catalog.json
    catalog_json = test_catalog_json()
    results.append(("GET /catalog.json", catalog_json))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed\n")
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} | {test_name}")
    
    # Check for 405 errors
    print("\n" + "=" * 80)
    print("405 ERROR CHECK (CRITICAL)")
    print("=" * 80)
    
    critical_tests = [
        ("POST /api/auth/register", results[0][1]),
        ("POST /api/quote", results[2][1])
    ]
    
    has_405 = not all(result for _, result in critical_tests)
    
    if has_405:
        print("\n⚠️  CRITICAL: Some endpoints returned 405 errors!")
        print("The Vercel rewrite fix is NOT working correctly.")
    else:
        print("\n✓ SUCCESS: No 405 errors detected!")
        print("All critical endpoints (register, quote) are working correctly.")
        print("The Vercel rewrite fix is VERIFIED at the backend level.")
    
    print("\n" + "=" * 80)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())

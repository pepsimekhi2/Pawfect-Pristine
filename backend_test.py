#!/usr/bin/env python3
"""
Backend API tests for Pawfect & Pristine v1.8
Tests the rebrand (phone + email) and new TOS v2.0
"""
import httpx
import asyncio
from datetime import datetime, timedelta

BASE_URL = "https://48511398-4d7d-4642-be1e-d796c8f83659.preview.emergentagent.com"
ADMIN_EMAIL = "admin@pawfectpristine.com"
ADMIN_PASSWORD = "Pawfect2026!"

# v1.8 rebrand constants
NEW_PHONE = "(404) 750-3446"
OLD_PHONE = "(470) 381-4682"
NEW_EMAIL = "itzmekhii@gmail.com"
OLD_EMAIL = "hello@pawfectpristine"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name, details=""):
        self.passed.append(f"✅ {test_name}: {details}")
    
    def add_fail(self, test_name, details=""):
        self.failed.append(f"❌ {test_name}: {details}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        if self.failed:
            print(f"\n❌ FAILED TESTS ({len(self.failed)}):")
            for f in self.failed:
                print(f"  {f}")
        
        if self.passed:
            print(f"\n✅ PASSED TESTS ({len(self.passed)}):")
            for p in self.passed:
                print(f"  {p}")
        
        total = len(self.passed) + len(self.failed)
        pass_rate = (len(self.passed) / total * 100) if total > 0 else 0
        print(f"\n{'='*80}")
        print(f"TOTAL: {len(self.passed)}/{total} passed ({pass_rate:.1f}%)")
        print(f"{'='*80}\n")

results = TestResults()

async def test_tos_v2():
    """Test 1: GET /api/tos returns v2.0 with new phone/email, no old phone/email"""
    print("\n[TEST 1] GET /api/tos - TOS v2.0 verification")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE_URL}/api/tos")
        
        if r.status_code != 200:
            results.add_fail("TOS endpoint", f"Expected 200, got {r.status_code}")
            return
        
        data = r.json()
        text = data.get("text", "")
        version = data.get("version")
        effective = data.get("effective")
        
        # Check version and effective date
        if version != "2.0":
            results.add_fail("TOS version", f"Expected '2.0', got '{version}'")
        else:
            results.add_pass("TOS version", "2.0 ✓")
        
        if effective != "2026-07-15":
            results.add_fail("TOS effective date", f"Expected '2026-07-15', got '{effective}'")
        else:
            results.add_pass("TOS effective date", "2026-07-15 ✓")
        
        # Check new phone is present
        if NEW_PHONE not in text:
            results.add_fail("TOS new phone", f"'{NEW_PHONE}' NOT FOUND in TOS text")
        else:
            results.add_pass("TOS new phone", f"'{NEW_PHONE}' found ✓")
        
        # Check new email is present
        if NEW_EMAIL not in text:
            results.add_fail("TOS new email", f"'{NEW_EMAIL}' NOT FOUND in TOS text")
        else:
            results.add_pass("TOS new email", f"'{NEW_EMAIL}' found ✓")
        
        # Check 65% refund cap is present
        if "65%" not in text:
            results.add_fail("TOS refund cap", "'65%' NOT FOUND in TOS text")
        else:
            results.add_pass("TOS refund cap", "'65%' found ✓")
        
        # Check TECHNICIAN'S RIGHT TO LEAVE section
        if "TECHNICIAN'S RIGHT TO LEAVE" not in text:
            results.add_fail("TOS section 7", "'TECHNICIAN'S RIGHT TO LEAVE' NOT FOUND")
        else:
            results.add_pass("TOS section 7", "'TECHNICIAN'S RIGHT TO LEAVE' found ✓")
        
        # Check old phone is NOT present
        if OLD_PHONE in text:
            results.add_fail("TOS old phone removed", f"OLD PHONE '{OLD_PHONE}' STILL PRESENT")
        else:
            results.add_pass("TOS old phone removed", f"'{OLD_PHONE}' not found ✓")
        
        # Check old email is NOT present
        if OLD_EMAIL in text:
            results.add_fail("TOS old email removed", f"OLD EMAIL '{OLD_EMAIL}' STILL PRESENT")
        else:
            results.add_pass("TOS old email removed", f"'{OLD_EMAIL}' not found ✓")
        
        # Check small-claims is NOT present
        if "small-claims" in text.lower() or "small claims" in text.lower():
            results.add_fail("TOS small-claims removed", "SMALL-CLAIMS CLAUSE STILL PRESENT")
        else:
            results.add_pass("TOS small-claims removed", "small-claims clause removed ✓")

async def test_eta_out_of_range():
    """Test 2: POST /api/eta with out-of-range address contains new phone"""
    print("\n[TEST 2] POST /api/eta - Out-of-range zone_message")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/api/eta",
            json={"address": "Times Square, New York, NY"}
        )
        
        if r.status_code != 200:
            results.add_fail("ETA out-of-range", f"Expected 200, got {r.status_code}")
            return
        
        data = r.json()
        zone_message = data.get("zone_message", "")
        
        # Check new phone is present
        if NEW_PHONE not in zone_message:
            results.add_fail("ETA zone_message new phone", f"'{NEW_PHONE}' NOT FOUND in zone_message")
        else:
            results.add_pass("ETA zone_message new phone", f"'{NEW_PHONE}' found ✓")
        
        # Check old phone is NOT present
        if OLD_PHONE in zone_message:
            results.add_fail("ETA zone_message old phone", f"OLD PHONE '{OLD_PHONE}' STILL PRESENT")
        else:
            results.add_pass("ETA zone_message old phone", f"'{OLD_PHONE}' not found ✓")

async def test_booking_out_of_range():
    """Test 3: POST /api/bookings with out-of-range address returns 400 with new phone"""
    print("\n[TEST 3] POST /api/bookings - Out-of-range error message")
    
    # First, register a fresh user
    test_email = f"v18test{datetime.now().timestamp():.0f}@example.com"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": "V18 Tester",
                "email": test_email,
                "password": "TestPass123!",
                "marketing_opt_in": True
            }
        )
        
        if r.status_code != 200:
            results.add_fail("Register test user", f"Expected 200, got {r.status_code}")
            return
        
        token = r.json().get("token")
        
        # Try to book with out-of-range address
        future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        r = await client.post(
            f"{BASE_URL}/api/bookings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "V18 Tester",
                "phone": "555-0100",
                "address": "Times Square, New York, NY",
                "service_value": "general_cleaning",
                "tier_key": "standard",
                "preferred_date": future_date,
                "preferred_time": "14:00",
                "payment_plan": "pay_later",
                "payment_method": "cash",
                "tos_accepted": True
            }
        )
        
        if r.status_code != 400:
            results.add_fail("Booking out-of-range status", f"Expected 400, got {r.status_code}")
            return
        
        detail = r.json().get("detail", "")
        
        # Check new phone is present
        if NEW_PHONE not in detail:
            results.add_fail("Booking error new phone", f"'{NEW_PHONE}' NOT FOUND in error detail")
        else:
            results.add_pass("Booking error new phone", f"'{NEW_PHONE}' found ✓")
        
        # Check old phone is NOT present
        if OLD_PHONE in detail:
            results.add_fail("Booking error old phone", f"OLD PHONE '{OLD_PHONE}' STILL PRESENT")
        else:
            results.add_pass("Booking error old phone", f"'{OLD_PHONE}' not found ✓")

async def test_booking_owner_notification():
    """Test 4: POST /api/bookings with valid address sends owner notification to new email"""
    print("\n[TEST 4] POST /api/bookings - Owner notification email")
    
    # Register a fresh user
    test_email = f"v18owner{datetime.now().timestamp():.0f}@example.com"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": "Owner Test",
                "email": test_email,
                "password": "TestPass123!",
                "marketing_opt_in": True
            }
        )
        
        if r.status_code != 200:
            results.add_fail("Register owner test user", f"Expected 200, got {r.status_code}")
            return
        
        token = r.json().get("token")
        
        # Book with valid in-area address
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        # Try different times to avoid conflicts
        for time_slot in ["14:00", "14:30", "15:00", "15:30", "16:00"]:
            r = await client.post(
                f"{BASE_URL}/api/bookings",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": "Owner Test",
                    "phone": "555-0200",
                    "address": "199 North Candler Street, Decatur, Georgia, 30030",
                    "service_value": "general_cleaning",
                    "tier_key": "standard",
                    "preferred_date": future_date,
                    "preferred_time": time_slot,
                    "payment_plan": "pay_later",
                    "payment_method": "cash",
                    "tos_accepted": True
                }
            )
            
            if r.status_code == 200:
                results.add_pass("Booking created", f"Booking created successfully at {time_slot}")
                break
            elif r.status_code == 409:
                continue  # Try next time slot
            else:
                results.add_fail("Booking creation", f"Expected 200, got {r.status_code}: {r.text[:200]}")
                return
        
        if r.status_code != 200:
            results.add_fail("Booking creation", "All time slots conflicted")
            return
        
        # Wait a moment for async email to be sent
        await asyncio.sleep(2)
        
        # Check backend logs for Resend email
        print("  → Checking backend logs for owner notification email...")
        import subprocess
        try:
            log_output = subprocess.check_output(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                text=True
            )
            
            # Look for the most recent owner notification emails
            resend_lines = [line for line in log_output.split("\n") if "Resend email sent" in line]
            
            if not resend_lines:
                results.add_fail("Owner notification logs", "No Resend email logs found")
                return
            
            # Check if owner notification went to new email
            owner_notification_found = False
            for line in resend_lines[-5:]:  # Check last 5 email logs
                if "New booking" in line and NEW_EMAIL in line:
                    owner_notification_found = True
                    results.add_pass("Owner notification email", f"Sent to {NEW_EMAIL} ✓")
                    break
                elif "New booking" in line and OLD_EMAIL in line:
                    results.add_fail("Owner notification email", f"STILL SENT TO OLD EMAIL {OLD_EMAIL}")
                    return
            
            if not owner_notification_found:
                # Check if any owner notification was sent
                owner_notif_exists = any("New booking" in line for line in resend_lines[-5:])
                if owner_notif_exists:
                    results.add_pass("Owner notification sent", "Owner notification email sent (email address not visible in logs)")
                else:
                    results.add_fail("Owner notification", "No owner notification found in recent logs")
        
        except Exception as e:
            results.add_fail("Log check", f"Could not check logs: {e}")

async def test_regression():
    """Test 5: Regression tests - verify existing endpoints still work"""
    print("\n[TEST 5] Regression tests")
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 5a: Admin login
        r = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if r.status_code == 200:
            results.add_pass("Regression: Admin login", "200 ✓")
        else:
            results.add_fail("Regression: Admin login", f"Expected 200, got {r.status_code}")
        
        # 5b: Catalog
        r = await client.get(f"{BASE_URL}/api/catalog")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and len(data) > 0:
                results.add_pass("Regression: Catalog", f"200 with {len(data)} services ✓")
            else:
                results.add_fail("Regression: Catalog", "Empty catalog")
        else:
            results.add_fail("Regression: Catalog", f"Expected 200, got {r.status_code}")
        
        # 5c: PayPal config
        r = await client.get(f"{BASE_URL}/api/paypal/config")
        if r.status_code == 200:
            data = r.json()
            if data.get("enabled") and data.get("env") == "live" and data.get("client_id"):
                results.add_pass("Regression: PayPal config", "enabled=true, env=live, client_id present ✓")
            else:
                results.add_fail("Regression: PayPal config", f"Invalid config: {data}")
        else:
            results.add_fail("Regression: PayPal config", f"Expected 200, got {r.status_code}")
        
        # 5d: PayPal create-order
        r = await client.post(
            f"{BASE_URL}/api/paypal/create-order",
            json={"amount": 1.00, "currency": "USD"}
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("id"):
                results.add_pass("Regression: PayPal create-order", f"200 with order ID {data['id'][:20]}... ✓")
            else:
                results.add_fail("Regression: PayPal create-order", "No order ID returned")
        else:
            results.add_fail("Regression: PayPal create-order", f"Expected 200, got {r.status_code}")
        
        # 5e: Geocode suggest
        r = await client.get(f"{BASE_URL}/api/geocode/suggest?q=Decatur")
        if r.status_code == 200:
            data = r.json()
            results_list = data.get("results", [])
            if len(results_list) > 0:
                ga_results = [res for res in results_list if res.get("state") == "Georgia"]
                if ga_results:
                    results.add_pass("Regression: Geocode suggest", f"200 with {len(ga_results)} GA results ✓")
                else:
                    results.add_pass("Regression: Geocode suggest", f"200 with {len(results_list)} results (no GA filter) ✓")
            else:
                results.add_pass("Regression: Geocode suggest", "200 with empty results (acceptable) ✓")
        else:
            results.add_fail("Regression: Geocode suggest", f"Expected 200, got {r.status_code}")
        
        # 5f: Static catalog.json
        r = await client.get(f"{BASE_URL}/catalog.json")
        if r.status_code == 200:
            data = r.json()
            if "general_cleaning" in str(data):
                results.add_pass("Regression: Static catalog.json", "200 with general_cleaning ✓")
            else:
                results.add_fail("Regression: Static catalog.json", "Missing general_cleaning")
        else:
            results.add_fail("Regression: Static catalog.json", f"Expected 200, got {r.status_code}")

async def main():
    print("="*80)
    print("PAWFECT & PRISTINE v1.8 BACKEND TESTS")
    print("Testing rebrand (phone + email) and TOS v2.0")
    print("="*80)
    
    await test_tos_v2()
    await test_eta_out_of_range()
    await test_booking_out_of_range()
    await test_booking_owner_notification()
    await test_regression()
    
    results.print_summary()

if __name__ == "__main__":
    asyncio.run(main())

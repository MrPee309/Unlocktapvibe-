#!/usr/bin/env python3
"""
UnlockTap Backend Regression Test Suite
Tests MongoDB connection robustness fix and all core endpoints
"""

import requests
import json
import random
import string
from datetime import datetime

# Base URL from .env
BASE_URL = "https://device-verify-check.preview.emergentagent.com/api"

def generate_random_string(length=8):
    """Generate random string for unique test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_test(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")

def test_health_endpoint():
    """Test 1: GET /api/health - should return 200 with specific fields"""
    print("\n=== TEST 1: Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        
        # Check status code
        if response.status_code != 200:
            print_test("Health endpoint status code", False, f"Expected 200, got {response.status_code}")
            return False
        
        # Check required fields
        checks = [
            ("status field", "status" in data and data["status"] == "ok"),
            ("db field", "db" in data and data["db"] == "connected"),
            ("env object", "env" in data and isinstance(data["env"], dict)),
            ("hasMongoUrl", data.get("env", {}).get("hasMongoUrl") == True),
            ("hasDbName", data.get("env", {}).get("hasDbName") == True),
            ("dbName present", data.get("env", {}).get("dbName") is not None),
            ("usersCount", "usersCount" in data and isinstance(data["usersCount"], int)),
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            if not check_result:
                print_test(f"Health endpoint - {check_name}", False, f"Data: {json.dumps(data, indent=2)}")
                all_passed = False
        
        if all_passed:
            print_test("Health endpoint", True, f"usersCount={data['usersCount']}, dbName={data['env']['dbName']}")
        
        return all_passed
    except Exception as e:
        print_test("Health endpoint", False, f"Exception: {str(e)}")
        return False

def test_root_endpoint():
    """Test 2: GET /api/ - should return 200 with status ok"""
    print("\n=== TEST 2: Root Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            print_test("Root endpoint status code", False, f"Expected 200, got {response.status_code}")
            return False
        
        if data.get("status") != "ok":
            print_test("Root endpoint status", False, f"Expected status='ok', got {data}")
            return False
        
        print_test("Root endpoint", True, f"Response: {data}")
        return True
    except Exception as e:
        print_test("Root endpoint", False, f"Exception: {str(e)}")
        return False

def test_auth_registration():
    """Test 3: POST /api/auth/register - full profile registration"""
    print("\n=== TEST 3: Auth Registration ===")
    results = []
    
    # Test 3a: Valid registration with all 6 fields
    try:
        unique_id = generate_random_string(10)
        payload = {
            "name": f"Test User {unique_id}",
            "username": f"testuser{unique_id}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test{unique_id}@example.com",
            "password": "Test@123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and "token" in data and "user" in data:
            user = data["user"]
            checks = [
                user.get("name") == payload["name"],
                user.get("username") == payload["username"],
                user.get("country") == payload["country"],
                user.get("phone") == payload["phone"],
                user.get("email") == payload["email"],
                user.get("credits") == 3,
                user.get("role") == "user",
                "password" not in user
            ]
            if all(checks):
                print_test("Valid registration", True, f"User created with 3 credits, no password field")
                results.append(True)
                # Save for later tests
                global test_user_token, test_user_email, test_user_password
                test_user_token = data["token"]
                test_user_email = payload["email"]
                test_user_password = payload["password"]
            else:
                print_test("Valid registration", False, f"User data validation failed: {user}")
                results.append(False)
        else:
            print_test("Valid registration", False, f"Status {response.status_code}, data: {data}")
            results.append(False)
    except Exception as e:
        print_test("Valid registration", False, f"Exception: {str(e)}")
        results.append(False)
    
    # Test 3b: Duplicate email -> 409
    try:
        payload = {
            "name": "Duplicate Test",
            "username": f"dupuser{generate_random_string(8)}",
            "country": "USA",
            "phone": "+1234567890",
            "email": test_user_email,  # Same email as above
            "password": "Test@123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        if response.status_code == 409:
            print_test("Duplicate email rejection", True, "Returns 409")
            results.append(True)
        else:
            print_test("Duplicate email rejection", False, f"Expected 409, got {response.status_code}")
            results.append(False)
    except Exception as e:
        print_test("Duplicate email rejection", False, f"Exception: {str(e)}")
        results.append(False)
    
    # Test 3c: Duplicate username (case-insensitive) -> 409
    try:
        unique_id = generate_random_string(10)
        username = f"uniqueuser{unique_id}"
        # First registration
        payload1 = {
            "name": "User One",
            "username": username.lower(),
            "country": "USA",
            "phone": "+1234567890",
            "email": f"user1{unique_id}@example.com",
            "password": "Test@123"
        }
        response1 = requests.post(f"{BASE_URL}/auth/register", json=payload1, timeout=10)
        
        # Second registration with same username (different case)
        payload2 = {
            "name": "User Two",
            "username": username.upper(),  # Same username, different case
            "country": "USA",
            "phone": "+1234567890",
            "email": f"user2{unique_id}@example.com",
            "password": "Test@123"
        }
        response2 = requests.post(f"{BASE_URL}/auth/register", json=payload2, timeout=10)
        
        if response1.status_code == 200 and response2.status_code == 409:
            print_test("Duplicate username rejection", True, "Case-insensitive check works")
            results.append(True)
        else:
            print_test("Duplicate username rejection", False, f"First: {response1.status_code}, Second: {response2.status_code}")
            results.append(False)
    except Exception as e:
        print_test("Duplicate username rejection", False, f"Exception: {str(e)}")
        results.append(False)
    
    # Test 3d: Missing field -> 400
    try:
        payload = {
            "name": "Test User",
            "username": "testuser",
            "country": "USA",
            "phone": "+1234567890",
            # Missing email and password
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        if response.status_code == 400:
            print_test("Missing field rejection", True, "Returns 400")
            results.append(True)
        else:
            print_test("Missing field rejection", False, f"Expected 400, got {response.status_code}")
            results.append(False)
    except Exception as e:
        print_test("Missing field rejection", False, f"Exception: {str(e)}")
        results.append(False)
    
    return all(results)

def test_auth_login():
    """Test 4: POST /api/auth/login"""
    print("\n=== TEST 4: Auth Login ===")
    results = []
    
    # Test 4a: Valid login
    try:
        payload = {
            "email": test_user_email,
            "password": test_user_password
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and "token" in data and "user" in data:
            print_test("Valid login", True, "Returns token and user")
            results.append(True)
        else:
            print_test("Valid login", False, f"Status {response.status_code}, data: {data}")
            results.append(False)
    except Exception as e:
        print_test("Valid login", False, f"Exception: {str(e)}")
        results.append(False)
    
    # Test 4b: Wrong password -> 401
    try:
        payload = {
            "email": test_user_email,
            "password": "WrongPassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        if response.status_code == 401:
            print_test("Wrong password rejection", True, "Returns 401")
            results.append(True)
        else:
            print_test("Wrong password rejection", False, f"Expected 401, got {response.status_code}")
            results.append(False)
    except Exception as e:
        print_test("Wrong password rejection", False, f"Exception: {str(e)}")
        results.append(False)
    
    return all(results)

def test_auth_me():
    """Test 5: GET /api/auth/me"""
    print("\n=== TEST 5: Auth Me Endpoint ===")
    results = []
    
    # Test 5a: With valid token -> 200
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and "user" in data:
            print_test("Auth me with token", True, "Returns user data")
            results.append(True)
        else:
            print_test("Auth me with token", False, f"Status {response.status_code}, data: {data}")
            results.append(False)
    except Exception as e:
        print_test("Auth me with token", False, f"Exception: {str(e)}")
        results.append(False)
    
    # Test 5b: Without token -> 401
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        if response.status_code == 401:
            print_test("Auth me without token", True, "Returns 401")
            results.append(True)
        else:
            print_test("Auth me without token", False, f"Expected 401, got {response.status_code}")
            results.append(False)
    except Exception as e:
        print_test("Auth me without token", False, f"Exception: {str(e)}")
        results.append(False)
    
    return all(results)

def test_admin_login():
    """Test 6: Admin login"""
    print("\n=== TEST 6: Admin Login ===")
    try:
        payload = {
            "email": "admin@unlocktap.com",
            "password": "Admin@123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get("user", {}).get("role") == "admin":
            print_test("Admin login", True, "Admin role verified")
            return True
        else:
            print_test("Admin login", False, f"Status {response.status_code}, role: {data.get('user', {}).get('role')}")
            return False
    except Exception as e:
        print_test("Admin login", False, f"Exception: {str(e)}")
        return False

def test_plans_endpoint():
    """Test 7: GET /api/plans"""
    print("\n=== TEST 7: Plans Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/plans", timeout=10)
        data = response.json()
        
        if response.status_code == 200 and "plans" in data:
            plans = data["plans"]
            if len(plans) == 4:
                print_test("Plans endpoint", True, f"Returns 4 plans: {[p['id'] for p in plans]}")
                return True
            else:
                print_test("Plans endpoint", False, f"Expected 4 plans, got {len(plans)}")
                return False
        else:
            print_test("Plans endpoint", False, f"Status {response.status_code}, data: {data}")
            return False
    except Exception as e:
        print_test("Plans endpoint", False, f"Exception: {str(e)}")
        return False

def test_imei_check():
    """Test 8: POST /api/imei/check"""
    print("\n=== TEST 8: IMEI Check ===")
    try:
        payload = {"imei": "359876543210987"}
        response = requests.post(f"{BASE_URL}/imei/check", json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            checks = [
                "searchId" in data,
                "free" in data,
                "locked" in data and data["locked"] == True,
                "Brand" in data.get("free", {}),
                "Model" in data.get("free", {}),
            ]
            if all(checks):
                print_test("IMEI check", True, f"searchId={data['searchId']}, model={data['free']['Model']}")
                global test_imei_search_id
                test_imei_search_id = data["searchId"]
                return True
            else:
                print_test("IMEI check", False, f"Missing required fields: {data}")
                return False
        else:
            print_test("IMEI check", False, f"Status {response.status_code}, data: {data}")
            return False
    except Exception as e:
        print_test("IMEI check", False, f"Exception: {str(e)}")
        return False

def test_serial_check():
    """Test 9: POST /api/serial/check"""
    print("\n=== TEST 9: Serial Check ===")
    try:
        payload = {"serial": "C39XY0ABJCLF"}
        response = requests.post(f"{BASE_URL}/serial/check", json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            checks = [
                "searchId" in data,
                "free" in data,
                "locked" in data and data["locked"] == True,
                "Brand" in data.get("free", {}),
                "Model" in data.get("free", {}),
            ]
            if all(checks):
                print_test("Serial check", True, f"searchId={data['searchId']}, model={data['free']['Model']}")
                return True
            else:
                print_test("Serial check", False, f"Missing required fields: {data}")
                return False
        else:
            print_test("Serial check", False, f"Status {response.status_code}, data: {data}")
            return False
    except Exception as e:
        print_test("Serial check", False, f"Exception: {str(e)}")
        return False

def test_unlock_endpoint():
    """Test 10: POST /api/unlock"""
    print("\n=== TEST 10: Unlock Endpoint ===")
    results = []
    
    # First, create a fresh user with credits
    try:
        unique_id = generate_random_string(10)
        payload = {
            "name": f"Unlock Test User {unique_id}",
            "username": f"unlockuser{unique_id}",
            "country": "USA",
            "phone": "+1234567890",
            "email": f"unlock{unique_id}@example.com",
            "password": "Test@123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        data = response.json()
        unlock_token = data["token"]
        
        # Do an IMEI check to get a searchId
        imei_payload = {"imei": "123456789012345"}
        headers = {"Authorization": f"Bearer {unlock_token}"}
        imei_response = requests.post(f"{BASE_URL}/imei/check", json=imei_payload, headers=headers, timeout=10)
        imei_data = imei_response.json()
        search_id = imei_data["searchId"]
        
        # Now unlock it
        unlock_payload = {"searchId": search_id}
        unlock_response = requests.post(f"{BASE_URL}/unlock", json=unlock_payload, headers=headers, timeout=10)
        unlock_data = unlock_response.json()
        
        if unlock_response.status_code == 200:
            checks = [
                "premium" in unlock_data,
                "credits" in unlock_data,
                unlock_data["credits"] == 2,  # Should be 3 - 1 = 2
            ]
            if all(checks):
                print_test("Unlock endpoint", True, f"Credits deducted: 3 -> 2, premium data returned")
                results.append(True)
            else:
                print_test("Unlock endpoint", False, f"Data validation failed: {unlock_data}")
                results.append(False)
        else:
            print_test("Unlock endpoint", False, f"Status {unlock_response.status_code}, data: {unlock_data}")
            results.append(False)
    except Exception as e:
        print_test("Unlock endpoint", False, f"Exception: {str(e)}")
        results.append(False)
    
    return all(results)

def test_protected_endpoints():
    """Test 11: Protected endpoints (dashboard, history, reports, orders)"""
    print("\n=== TEST 11: Protected Endpoints ===")
    results = []
    
    endpoints = [
        "/dashboard",
        "/history",
        "/reports",
        "/orders"
    ]
    
    # Test with valid token -> 200
    headers = {"Authorization": f"Bearer {test_user_token}"}
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            if response.status_code == 200:
                print_test(f"{endpoint} with token", True, "Returns 200")
                results.append(True)
            else:
                print_test(f"{endpoint} with token", False, f"Expected 200, got {response.status_code}")
                results.append(False)
        except Exception as e:
            print_test(f"{endpoint} with token", False, f"Exception: {str(e)}")
            results.append(False)
    
    # Test without token -> 401
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 401:
                print_test(f"{endpoint} without token", True, "Returns 401")
                results.append(True)
            else:
                print_test(f"{endpoint} without token", False, f"Expected 401, got {response.status_code}")
                results.append(False)
        except Exception as e:
            print_test(f"{endpoint} without token", False, f"Exception: {str(e)}")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("=" * 60)
    print("UnlockTap Backend Regression Test Suite")
    print("Testing MongoDB connection robustness fix")
    print("=" * 60)
    
    # Initialize global variables
    global test_user_token, test_user_email, test_user_password, test_imei_search_id
    test_user_token = None
    test_user_email = None
    test_user_password = None
    test_imei_search_id = None
    
    results = []
    
    # Run tests in order
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Auth Registration", test_auth_registration()))
    results.append(("Auth Login", test_auth_login()))
    results.append(("Auth Me", test_auth_me()))
    results.append(("Admin Login", test_admin_login()))
    results.append(("Plans Endpoint", test_plans_endpoint()))
    results.append(("IMEI Check", test_imei_check()))
    results.append(("Serial Check", test_serial_check()))
    results.append(("Unlock Endpoint", test_unlock_endpoint()))
    results.append(("Protected Endpoints", test_protected_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed ({passed*100//total}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Backend is working correctly after MongoDB fix.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the failures above.")
        return 1

if __name__ == "__main__":
    exit(main())

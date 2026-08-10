#!/usr/bin/env python3
"""
UnlockTap Backend API Test Suite
Tests Terms & Conditions enforcement + MongoDB env standardization + full customer flow
"""

import requests
import json
import random
import string
from datetime import datetime

# Base URL from environment
BASE_URL = "https://device-verify-check.preview.emergentagent.com/api"

def random_string(length=8):
    """Generate random string for unique test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_test(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")

def test_terms_enforcement():
    """Test 1: Terms & Conditions MANDATORY enforcement"""
    print("\n" + "="*80)
    print("TEST 1: TERMS & CONDITIONS ENFORCEMENT")
    print("="*80)
    
    test_email = f"termstest_{random_string()}@test.com"
    test_username = f"termsuser_{random_string()}"
    
    # Test 1a: Register WITHOUT termsAccepted (missing field)
    print("\n1a. Register WITHOUT termsAccepted field (should return 400)")
    payload = {
        "name": "Terms Test User",
        "username": test_username,
        "country": "United States",
        "phone": "+1234567890",
        "email": test_email,
        "password": "Test@123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    expected_error = "You must agree to the Terms & Conditions and Privacy Policy to create an account."
    
    if response.status_code == 400:
        error_msg = response.json().get('error', '')
        if error_msg == expected_error:
            print_test("Register without termsAccepted returns 400 with EXACT error message", True, f"Error: '{error_msg}'")
        else:
            print_test("Register without termsAccepted returns 400 but WRONG error message", False, f"Expected: '{expected_error}', Got: '{error_msg}'")
    else:
        print_test("Register without termsAccepted", False, f"Expected 400, got {response.status_code}")
    
    # Test 1b: Register with termsAccepted=false
    print("\n1b. Register with termsAccepted=false (should return 400)")
    payload["termsAccepted"] = False
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    if response.status_code == 400:
        error_msg = response.json().get('error', '')
        if error_msg == expected_error:
            print_test("Register with termsAccepted=false returns 400 with EXACT error message", True, f"Error: '{error_msg}'")
        else:
            print_test("Register with termsAccepted=false returns 400 but WRONG error message", False, f"Expected: '{expected_error}', Got: '{error_msg}'")
    else:
        print_test("Register with termsAccepted=false", False, f"Expected 400, got {response.status_code}")
    
    # Test 1c: Register with termsAccepted=true (should succeed)
    print("\n1c. Register with termsAccepted=true (should return 200)")
    payload["termsAccepted"] = True
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        user = data.get('user')
        
        # Verify token exists
        has_token = bool(token)
        print_test("Registration returns token", has_token, f"Token: {'present' if has_token else 'missing'}")
        
        # Verify user object
        has_user = bool(user)
        print_test("Registration returns user object", has_user)
        
        if user:
            # Verify termsAccepted field
            terms_accepted = user.get('termsAccepted')
            print_test("User has termsAccepted=true", terms_accepted == True, f"termsAccepted: {terms_accepted}")
            
            # Verify termsAcceptedAt timestamp
            terms_accepted_at = user.get('termsAcceptedAt')
            has_timestamp = bool(terms_accepted_at)
            print_test("User has termsAcceptedAt timestamp", has_timestamp, f"termsAcceptedAt: {terms_accepted_at}")
            
            # Verify NO password field in response
            has_password = 'password' in user
            print_test("User object does NOT contain password field", not has_password, f"Password field present: {has_password}")
            
            # Verify all profile fields present
            required_fields = ['name', 'username', 'country', 'phone', 'email', 'credits', 'role']
            missing_fields = [f for f in required_fields if f not in user]
            print_test("User object contains all profile fields", len(missing_fields) == 0, 
                      f"Missing: {missing_fields}" if missing_fields else "All fields present")
            
            # Verify credits = 3
            credits = user.get('credits')
            print_test("User has 3 free credits", credits == 3, f"Credits: {credits}")
            
            # Verify role = user
            role = user.get('role')
            print_test("User has role='user'", role == 'user', f"Role: {role}")
        
        return token, user
    else:
        print_test("Register with termsAccepted=true", False, f"Expected 200, got {response.status_code}: {response.text}")
        return None, None

def test_registration_validation():
    """Test 2: Registration validation regression"""
    print("\n" + "="*80)
    print("TEST 2: REGISTRATION VALIDATION REGRESSION")
    print("="*80)
    
    base_payload = {
        "name": "Valid User",
        "username": f"validuser_{random_string()}",
        "country": "United States",
        "phone": "+1234567890",
        "email": f"valid_{random_string()}@test.com",
        "password": "Test@123",
        "termsAccepted": True
    }
    
    # Test 2a: Missing required fields
    print("\n2a. Missing required fields (should return 400)")
    required_fields = ['name', 'username', 'country', 'phone', 'email', 'password']
    for field in required_fields:
        payload = base_payload.copy()
        del payload[field]
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        passed = response.status_code == 400
        print_test(f"Missing {field} returns 400", passed, f"Status: {response.status_code}")
    
    # Test 2b: Invalid username (too short)
    print("\n2b. Invalid username (too short, should return 400)")
    payload = base_payload.copy()
    payload["username"] = "ab"
    payload["email"] = f"test_{random_string()}@test.com"
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Username too short returns 400", response.status_code == 400, f"Status: {response.status_code}")
    
    # Test 2c: Invalid username (contains space)
    print("\n2c. Invalid username (contains space, should return 400)")
    payload = base_payload.copy()
    payload["username"] = "has space"
    payload["email"] = f"test_{random_string()}@test.com"
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Username with space returns 400", response.status_code == 400, f"Status: {response.status_code}")
    
    # Test 2d: Invalid username (too long)
    print("\n2d. Invalid username (too long, should return 400)")
    payload = base_payload.copy()
    payload["username"] = "a" * 21
    payload["email"] = f"test_{random_string()}@test.com"
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Username too long returns 400", response.status_code == 400, f"Status: {response.status_code}")
    
    # Test 2e: Invalid phone
    print("\n2e. Invalid phone (should return 400)")
    payload = base_payload.copy()
    payload["phone"] = "abc"
    payload["email"] = f"test_{random_string()}@test.com"
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Invalid phone returns 400", response.status_code == 400, f"Status: {response.status_code}")
    
    # Test 2f: Password too short
    print("\n2f. Password too short (should return 400)")
    payload = base_payload.copy()
    payload["password"] = "12345"
    payload["email"] = f"test_{random_string()}@test.com"
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Password < 6 chars returns 400", response.status_code == 400, f"Status: {response.status_code}")
    
    # Test 2g: Invalid email
    print("\n2g. Invalid email (should return 400)")
    payload = base_payload.copy()
    payload["email"] = "notanemail"
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Invalid email returns 400", response.status_code == 400, f"Status: {response.status_code}")
    
    # Test 2h: Duplicate email
    print("\n2h. Duplicate email (should return 409)")
    # First registration
    email = f"duplicate_{random_string()}@test.com"
    payload = base_payload.copy()
    payload["email"] = email
    payload["username"] = f"user1_{random_string()}"
    response1 = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    # Second registration with same email
    payload["username"] = f"user2_{random_string()}"
    response2 = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Duplicate email returns 409", response2.status_code == 409, f"Status: {response2.status_code}")
    
    # Test 2i: Duplicate username (case-insensitive)
    print("\n2i. Duplicate username case-insensitive (should return 409)")
    username = f"dupuser_{random_string()}"
    payload = base_payload.copy()
    payload["username"] = username.lower()
    payload["email"] = f"user1_{random_string()}@test.com"
    response1 = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    # Second registration with same username (uppercase)
    payload["username"] = username.upper()
    payload["email"] = f"user2_{random_string()}@test.com"
    response2 = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_test("Duplicate username (case-insensitive) returns 409", response2.status_code == 409, f"Status: {response2.status_code}")

def test_full_customer_flow():
    """Test 3: Full customer flow"""
    print("\n" + "="*80)
    print("TEST 3: FULL CUSTOMER FLOW")
    print("="*80)
    
    # Step 1: Register with termsAccepted=true
    print("\n3.1. Register new customer")
    email = f"customer_{random_string()}@test.com"
    username = f"customer_{random_string()}"
    password = "Customer@123"
    
    register_payload = {
        "name": "Customer Test",
        "username": username,
        "country": "United States",
        "phone": "+1234567890",
        "email": email,
        "password": password,
        "termsAccepted": True
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        user = data.get('user')
        print_test("Customer registration successful", True, f"User ID: {user.get('id')}")
    else:
        print_test("Customer registration", False, f"Status: {response.status_code}")
        return
    
    # Step 2: Login
    print("\n3.2. Login with email and password")
    login_payload = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print_test("Login successful", True, f"Token received")
    else:
        print_test("Login", False, f"Status: {response.status_code}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: GET /auth/me
    print("\n3.3. GET /auth/me with Bearer token")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        user = response.json().get('user')
        has_password = 'password' in user if user else True
        print_test("GET /auth/me returns user", True, f"No password field: {not has_password}")
    else:
        print_test("GET /auth/me", False, f"Status: {response.status_code}")
    
    # Step 4: GET /api/dashboard
    print("\n3.4. GET /api/dashboard")
    response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    if response.status_code == 200:
        data = response.json()
        stats = data.get('stats', {})
        print_test("GET /dashboard returns stats", True, f"Credits: {stats.get('credits')}")
    else:
        print_test("GET /dashboard", False, f"Status: {response.status_code}")
    
    # Step 5: POST /api/imei/check
    print("\n3.5. POST /api/imei/check")
    imei_payload = {"imei": "359876543210987"}
    response = requests.post(f"{BASE_URL}/imei/check", json=imei_payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        search_id = data.get('searchId')
        print_test("IMEI check successful", True, f"SearchId: {search_id}")
    else:
        print_test("IMEI check", False, f"Status: {response.status_code}")
        return
    
    # Step 6: POST /api/unlock
    print("\n3.6. POST /api/unlock (should deduct 1 credit)")
    unlock_payload = {"searchId": search_id}
    response = requests.post(f"{BASE_URL}/unlock", json=unlock_payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        credits = data.get('credits')
        print_test("Unlock successful", True, f"Credits after unlock: {credits} (should be 2)")
    else:
        print_test("Unlock", False, f"Status: {response.status_code}")
    
    # Step 7: GET /api/plans
    print("\n3.7. GET /api/plans")
    response = requests.get(f"{BASE_URL}/plans")
    if response.status_code == 200:
        data = response.json()
        plans = data.get('plans', [])
        print_test("GET /plans returns 4 plans", len(plans) == 4, f"Plans count: {len(plans)}")
    else:
        print_test("GET /plans", False, f"Status: {response.status_code}")
    
    # Step 8: GET /api/orders
    print("\n3.8. GET /api/orders")
    response = requests.get(f"{BASE_URL}/orders", headers=headers)
    if response.status_code == 200:
        data = response.json()
        orders = data.get('items', [])
        print_test("GET /orders successful", True, f"Orders count: {len(orders)}")
    else:
        print_test("GET /orders", False, f"Status: {response.status_code}")
    
    # Step 9: Test protected endpoints without token (should return 401)
    print("\n3.9. Test protected endpoints without token (should return 401)")
    protected_endpoints = [
        ("/auth/me", "GET"),
        ("/dashboard", "GET"),
        ("/history", "GET"),
        ("/reports", "GET"),
        ("/orders", "GET")
    ]
    
    for endpoint, method in protected_endpoints:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        else:
            response = requests.post(f"{BASE_URL}{endpoint}")
        
        passed = response.status_code == 401
        print_test(f"{method} {endpoint} without token returns 401", passed, f"Status: {response.status_code}")
    
    # Step 10: Test data isolation (create second user)
    print("\n3.10. Test data isolation (create second user)")
    email2 = f"customer2_{random_string()}@test.com"
    username2 = f"customer2_{random_string()}"
    password2 = "Customer2@123"
    
    register_payload2 = {
        "name": "Customer 2",
        "username": username2,
        "country": "Canada",
        "phone": "+1987654321",
        "email": email2,
        "password": password2,
        "termsAccepted": True
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload2)
    if response.status_code == 200:
        data = response.json()
        token2 = data.get('token')
        print_test("Second user registration successful", True)
        
        # Login as second user
        login_payload2 = {"email": email2, "password": password2}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_payload2)
        if response.status_code == 200:
            token2 = response.json().get('token')
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            # Check second user's history (should be empty)
            response = requests.get(f"{BASE_URL}/history", headers=headers2)
            if response.status_code == 200:
                items = response.json().get('items', [])
                print_test("Second user has empty history (data isolation)", len(items) == 0, f"History items: {len(items)}")
            
            # Check second user's reports (should be empty)
            response = requests.get(f"{BASE_URL}/reports", headers=headers2)
            if response.status_code == 200:
                items = response.json().get('items', [])
                print_test("Second user has empty reports (data isolation)", len(items) == 0, f"Report items: {len(items)}")
            
            # Check second user's orders (should be empty)
            response = requests.get(f"{BASE_URL}/orders", headers=headers2)
            if response.status_code == 200:
                items = response.json().get('items', [])
                print_test("Second user has empty orders (data isolation)", len(items) == 0, f"Order items: {len(items)}")

def test_health_mongo_diagnostics():
    """Test 4: Health endpoint and MongoDB diagnostics"""
    print("\n" + "="*80)
    print("TEST 4: HEALTH / MONGO DIAGNOSTICS")
    print("="*80)
    
    print("\n4.1. GET /api/health")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check status
        status = data.get('status')
        print_test("Health status is 'ok'", status == 'ok', f"Status: {status}")
        
        # Check db connection
        db = data.get('db')
        print_test("DB status is 'connected'", db == 'connected', f"DB: {db}")
        
        # Check env object
        env = data.get('env', {})
        print_test("Response contains env object", bool(env))
        
        if env:
            # Check mongoVarUsed
            mongo_var = env.get('mongoVarUsed')
            print_test("env.mongoVarUsed present", mongo_var is not None, f"mongoVarUsed: {mongo_var}")
            
            # Check hasMongoUrl
            has_mongo_url = env.get('hasMongoUrl')
            print_test("env.hasMongoUrl is boolean", isinstance(has_mongo_url, bool), f"hasMongoUrl: {has_mongo_url}")
            
            # Check hasMongoUri
            has_mongo_uri = env.get('hasMongoUri')
            print_test("env.hasMongoUri is boolean", isinstance(has_mongo_uri, bool), f"hasMongoUri: {has_mongo_uri}")
            
            # Check hasMongodbUri
            has_mongodb_uri = env.get('hasMongodbUri')
            print_test("env.hasMongodbUri is boolean", isinstance(has_mongodb_uri, bool), f"hasMongodbUri: {has_mongodb_uri}")
            
            # Check connection object
            connection = env.get('connection', {})
            print_test("env.connection object present", bool(connection))
            
            if connection:
                # Check host
                host = connection.get('host')
                print_test("env.connection.host present", host is not None, f"host: {host}")
                
                # Check hasPassword
                has_password = connection.get('hasPassword')
                print_test("env.connection.hasPassword is boolean", isinstance(has_password, bool), f"hasPassword: {has_password}")
        
        # Check usersCount
        users_count = data.get('usersCount')
        print_test("usersCount is numeric", isinstance(users_count, (int, float)), f"usersCount: {users_count}")
        
        # CRITICAL: Check NO raw password in response
        response_text = json.dumps(data)
        # Common password patterns to check
        suspicious_patterns = ['password:', 'pwd:', 'pass:']
        has_password_leak = any(pattern in response_text.lower() for pattern in suspicious_patterns)
        
        # Also check if there's any string that looks like a MongoDB password (contains @ and special chars)
        # This is a heuristic check - we're looking for connection strings with passwords
        import re
        # Pattern for mongodb://username:password@host
        password_pattern = r'mongodb(?:\+srv)?://[^:]+:([^@]+)@'
        password_match = re.search(password_pattern, response_text)
        
        print_test("NO raw MongoDB password in response", not has_password_leak and not password_match, 
                  "CRITICAL: Password leak detected!" if (has_password_leak or password_match) else "Password properly masked")
        
    else:
        print_test("GET /health", False, f"Status: {response.status_code}")

def test_admin_login():
    """Test 5: Admin login"""
    print("\n" + "="*80)
    print("TEST 5: ADMIN LOGIN")
    print("="*80)
    
    print("\n5.1. Admin login (admin@unlocktap.com / Admin@123)")
    login_payload = {
        "email": "admin@unlocktap.com",
        "password": "Admin@123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    
    if response.status_code == 200:
        data = response.json()
        user = data.get('user', {})
        role = user.get('role')
        print_test("Admin login successful with role='admin'", role == 'admin', f"Role: {role}")
    else:
        print_test("Admin login", False, f"Status: {response.status_code}")

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("UNLOCKTAP BACKEND API TEST SUITE")
    print("Terms & Conditions Enforcement + MongoDB Env Standardization")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Terms enforcement (PRIMARY)
        test_terms_enforcement()
        
        # Test 2: Registration validation regression
        test_registration_validation()
        
        # Test 3: Full customer flow
        test_full_customer_flow()
        
        # Test 4: Health / Mongo diagnostics
        test_health_mongo_diagnostics()
        
        # Test 5: Admin login
        test_admin_login()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

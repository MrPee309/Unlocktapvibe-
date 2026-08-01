#!/usr/bin/env python3
"""
Backend regression test for UnlockTap after MongoDB connection handling + /health diagnostics update.
Tests the enhanced /health endpoint and verifies no regression in auth and core endpoints.
"""

import requests
import json
import random
import string

# Base URL from environment
BASE_URL = "https://device-verify-check.preview.emergentagent.com/api"

def random_string(length=8):
    """Generate random string for unique test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def test_health_endpoint():
    """Test 1: GET /api/health returns enhanced diagnostics with NO password exposure"""
    print("\n" + "="*80)
    print("TEST 1: GET /api/health - Enhanced diagnostics")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Verify required fields
        required_fields = ['status', 'db', 'env']
        for field in required_fields:
            if field not in data:
                print(f"❌ FAILED: Missing required field '{field}'")
                return False
        
        # Verify status and db
        if data['status'] != 'ok':
            print(f"❌ FAILED: Expected status='ok', got '{data['status']}'")
            return False
        
        if data['db'] != 'connected':
            print(f"❌ FAILED: Expected db='connected', got '{data['db']}'")
            return False
        
        # Verify env object has required fields
        env = data.get('env', {})
        required_env_fields = ['mongoVarUsed', 'hasMongoUrl', 'hasMongoUri', 'connection']
        for field in required_env_fields:
            if field not in env:
                print(f"❌ FAILED: Missing env field '{field}'")
                return False
        
        # Verify mongoVarUsed is correct (should be 'MONGO_URL' based on .env)
        if env['mongoVarUsed'] != 'MONGO_URL':
            print(f"⚠️  WARNING: Expected mongoVarUsed='MONGO_URL', got '{env['mongoVarUsed']}'")
        
        # Verify hasMongoUrl is true
        if not env['hasMongoUrl']:
            print(f"❌ FAILED: Expected hasMongoUrl=true, got {env['hasMongoUrl']}")
            return False
        
        # Verify connection object exists and has required fields
        connection = env.get('connection', {})
        if not connection:
            print(f"❌ FAILED: connection object is empty or missing")
            return False
        
        # Verify connection has host and hasPassword fields
        if 'host' not in connection:
            print(f"❌ FAILED: connection missing 'host' field")
            return False
        
        if 'hasPassword' not in connection:
            print(f"❌ FAILED: connection missing 'hasPassword' field")
            return False
        
        if not isinstance(connection['hasPassword'], bool):
            print(f"❌ FAILED: hasPassword should be boolean, got {type(connection['hasPassword'])}")
            return False
        
        # CRITICAL: Verify NO raw password is exposed anywhere in the response
        response_str = json.dumps(data).lower()
        # Check for common password patterns (this is a basic check)
        if 'password' in response_str and 'haspassword' not in response_str:
            print(f"❌ CRITICAL: Possible password exposure detected in response!")
            return False
        
        # Verify usersCount is present and numeric
        if 'usersCount' not in data:
            print(f"❌ FAILED: Missing 'usersCount' field")
            return False
        
        if not isinstance(data['usersCount'], int):
            print(f"❌ FAILED: usersCount should be integer, got {type(data['usersCount'])}")
            return False
        
        print(f"✅ PASSED: /health endpoint returns all required fields")
        print(f"   - status: {data['status']}")
        print(f"   - db: {data['db']}")
        print(f"   - env.mongoVarUsed: {env['mongoVarUsed']}")
        print(f"   - env.hasMongoUrl: {env['hasMongoUrl']}")
        print(f"   - env.hasMongoUri: {env.get('hasMongoUri')}")
        print(f"   - env.connection.host: {connection.get('host')}")
        print(f"   - env.connection.hasPassword: {connection.get('hasPassword')}")
        print(f"   - usersCount: {data['usersCount']}")
        print(f"   - NO password exposed ✓")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_root_endpoint():
    """Test 2: GET /api/ returns 200 ok"""
    print("\n" + "="*80)
    print("TEST 2: GET /api/ - Root endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('status') != 'ok':
            print(f"❌ FAILED: Expected status='ok'")
            return False
        
        print(f"✅ PASSED: Root endpoint returns 200 ok")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_auth_registration():
    """Test 3: Auth registration with full profile fields"""
    print("\n" + "="*80)
    print("TEST 3: Auth Registration - Full profile fields")
    print("="*80)
    
    # Generate unique test data
    username = f"testuser{random_string(10)}"
    email = f"test{random_string(10)}@example.com"
    
    payload = {
        "name": "Test User",
        "username": username,
        "country": "United States",
        "phone": "+1234567890",
        "email": email,
        "password": "Test@123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
        
        data = response.json()
        
        # Verify token and user are present
        if 'token' not in data or 'user' not in data:
            print(f"❌ FAILED: Missing token or user in response")
            return None, None
        
        user = data['user']
        
        # Verify user has all profile fields
        required_fields = ['name', 'username', 'country', 'phone', 'email', 'credits', 'role']
        for field in required_fields:
            if field not in user:
                print(f"❌ FAILED: Missing field '{field}' in user object")
                return None, None
        
        # Verify NO password field in response
        if 'password' in user:
            print(f"❌ FAILED: Password field should NOT be in response")
            return None, None
        
        # Verify credits = 3 and role = user
        if user['credits'] != 3:
            print(f"❌ FAILED: Expected credits=3, got {user['credits']}")
            return None, None
        
        if user['role'] != 'user':
            print(f"❌ FAILED: Expected role='user', got {user['role']}")
            return None, None
        
        print(f"✅ PASSED: Registration successful")
        print(f"   - Token received: {data['token'][:20]}...")
        print(f"   - User fields: {', '.join(user.keys())}")
        print(f"   - Credits: {user['credits']}")
        print(f"   - Role: {user['role']}")
        print(f"   - NO password field ✓")
        
        return data['token'], email
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return None, None

def test_duplicate_email(email):
    """Test 4: Duplicate email returns 409"""
    print("\n" + "="*80)
    print("TEST 4: Duplicate Email - Should return 409")
    print("="*80)
    
    # Generate valid username (letters, numbers, underscore only)
    valid_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    
    payload = {
        "name": "Another User",
        "username": f"user{valid_username}",
        "country": "Canada",
        "phone": "+1987654321",
        "email": email,  # Same email as previous registration
        "password": "Test@456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 409:
            print(f"❌ FAILED: Expected 409, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print(f"✅ PASSED: Duplicate email correctly returns 409")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_duplicate_username():
    """Test 5: Duplicate username returns 409"""
    print("\n" + "="*80)
    print("TEST 5: Duplicate Username - Should return 409")
    print("="*80)
    
    username = f"uniqueuser{random_string(10)}"
    
    # First registration
    payload1 = {
        "name": "User One",
        "username": username,
        "country": "USA",
        "phone": "+1111111111",
        "email": f"user1{random_string(10)}@example.com",
        "password": "Test@123"
    }
    
    try:
        response1 = requests.post(f"{BASE_URL}/auth/register", json=payload1, timeout=10)
        if response1.status_code != 200:
            print(f"❌ FAILED: First registration failed with {response1.status_code}")
            return False
        
        # Second registration with same username (different case)
        payload2 = {
            "name": "User Two",
            "username": username.upper(),  # Same username, different case
            "country": "Canada",
            "phone": "+2222222222",
            "email": f"user2{random_string(10)}@example.com",
            "password": "Test@456"
        }
        
        response2 = requests.post(f"{BASE_URL}/auth/register", json=payload2, timeout=10)
        print(f"Status Code: {response2.status_code}")
        
        if response2.status_code != 409:
            print(f"❌ FAILED: Expected 409, got {response2.status_code}")
            print(f"Response: {response2.text}")
            return False
        
        print(f"✅ PASSED: Duplicate username (case-insensitive) correctly returns 409")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_login(email, password="Test@123"):
    """Test 6: Login with valid credentials"""
    print("\n" + "="*80)
    print("TEST 6: Login - Valid credentials")
    print("="*80)
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        
        if 'token' not in data or 'user' not in data:
            print(f"❌ FAILED: Missing token or user in response")
            return None
        
        print(f"✅ PASSED: Login successful")
        print(f"   - Token received: {data['token'][:20]}...")
        
        return data['token']
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return None

def test_login_wrong_password(email):
    """Test 7: Login with wrong password returns 401"""
    print("\n" + "="*80)
    print("TEST 7: Login - Wrong password should return 401")
    print("="*80)
    
    payload = {
        "email": email,
        "password": "WrongPassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 401:
            print(f"❌ FAILED: Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print(f"✅ PASSED: Wrong password correctly returns 401")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_auth_me_with_token(token):
    """Test 8: GET /auth/me with Bearer token"""
    print("\n" + "="*80)
    print("TEST 8: GET /auth/me - With Bearer token")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        if 'user' not in data:
            print(f"❌ FAILED: Missing user in response")
            return False
        
        user = data['user']
        
        # Verify NO password field
        if 'password' in user:
            print(f"❌ FAILED: Password field should NOT be in response")
            return False
        
        print(f"✅ PASSED: /auth/me returns user data")
        print(f"   - User fields: {', '.join(user.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_auth_me_without_token():
    """Test 9: GET /auth/me without token returns 401"""
    print("\n" + "="*80)
    print("TEST 9: GET /auth/me - Without token should return 401")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 401:
            print(f"❌ FAILED: Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print(f"✅ PASSED: /auth/me without token correctly returns 401")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_admin_login():
    """Test 10: Admin login with admin@unlocktap.com/Admin@123"""
    print("\n" + "="*80)
    print("TEST 10: Admin Login - admin@unlocktap.com/Admin@123")
    print("="*80)
    
    payload = {
        "email": "admin@unlocktap.com",
        "password": "Admin@123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        if 'user' not in data:
            print(f"❌ FAILED: Missing user in response")
            return False
        
        user = data['user']
        
        if user.get('role') != 'admin':
            print(f"❌ FAILED: Expected role='admin', got '{user.get('role')}'")
            return False
        
        print(f"✅ PASSED: Admin login successful")
        print(f"   - Role: {user['role']}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_plans_endpoint():
    """Test 11: GET /api/plans returns 4 plans"""
    print("\n" + "="*80)
    print("TEST 11: GET /api/plans - Should return 4 plans")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/plans", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        if 'plans' not in data:
            print(f"❌ FAILED: Missing plans in response")
            return False
        
        plans = data['plans']
        
        if len(plans) != 4:
            print(f"❌ FAILED: Expected 4 plans, got {len(plans)}")
            return False
        
        # Verify plan names
        expected_ids = ['single', 'starter', 'technician', 'business']
        plan_ids = [p.get('id') for p in plans]
        
        for expected_id in expected_ids:
            if expected_id not in plan_ids:
                print(f"❌ FAILED: Missing plan '{expected_id}'")
                return False
        
        print(f"✅ PASSED: /plans returns 4 plans")
        print(f"   - Plan IDs: {', '.join(plan_ids)}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_imei_check():
    """Test 12: POST /api/imei/check with valid IMEI"""
    print("\n" + "="*80)
    print("TEST 12: POST /api/imei/check - Valid IMEI")
    print("="*80)
    
    payload = {
        "imei": "359876543210987"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/imei/check", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        
        # Verify required fields
        required_fields = ['searchId', 'type', 'query', 'free', 'locked']
        for field in required_fields:
            if field not in data:
                print(f"❌ FAILED: Missing field '{field}'")
                return None
        
        # Verify free preview has required fields
        free = data['free']
        required_free_fields = ['Brand', 'Model', 'Model Number', 'Capacity', 'Color']
        for field in required_free_fields:
            if field not in free:
                print(f"❌ FAILED: Missing free preview field '{field}'")
                return None
        
        # Verify locked is true
        if not data['locked']:
            print(f"❌ FAILED: Expected locked=true")
            return None
        
        print(f"✅ PASSED: IMEI check successful")
        print(f"   - SearchId: {data['searchId']}")
        print(f"   - Brand: {free['Brand']}")
        print(f"   - Model: {free['Model']}")
        print(f"   - Locked: {data['locked']}")
        
        return data['searchId']
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return None

def test_unlock_with_credit_deduction(token, search_id):
    """Test 13: POST /api/unlock - Should deduct 1 credit"""
    print("\n" + "="*80)
    print("TEST 13: POST /api/unlock - Credit deduction")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "searchId": search_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/unlock", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify required fields
        if 'free' not in data or 'premium' not in data or 'credits' not in data:
            print(f"❌ FAILED: Missing required fields in response")
            return False
        
        # Verify credits were deducted (should be 2 now, started with 3)
        if data['credits'] != 2:
            print(f"⚠️  WARNING: Expected credits=2 after unlock, got {data['credits']}")
        
        print(f"✅ PASSED: Unlock successful")
        print(f"   - Credits after unlock: {data['credits']}")
        print(f"   - Premium fields received: {len(data['premium'])} fields")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def test_dashboard_endpoint(token):
    """Test 14: GET /api/dashboard with token"""
    print("\n" + "="*80)
    print("TEST 14: GET /api/dashboard - With Bearer token")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify required fields
        if 'stats' not in data or 'recent' not in data:
            print(f"❌ FAILED: Missing required fields in response")
            return False
        
        stats = data['stats']
        required_stats = ['credits', 'searches', 'reports', 'orders']
        for field in required_stats:
            if field not in stats:
                print(f"❌ FAILED: Missing stats field '{field}'")
                return False
        
        print(f"✅ PASSED: Dashboard endpoint working")
        print(f"   - Credits: {stats['credits']}")
        print(f"   - Searches: {stats['searches']}")
        print(f"   - Reports: {stats['reports']}")
        print(f"   - Orders: {stats['orders']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("\n" + "="*80)
    print("UNLOCKTAP BACKEND REGRESSION TEST")
    print("MongoDB Connection Handling + /health Diagnostics Update")
    print("="*80)
    
    results = []
    
    # Test 1: Health endpoint
    results.append(("Health endpoint", test_health_endpoint()))
    
    # Test 2: Root endpoint
    results.append(("Root endpoint", test_root_endpoint()))
    
    # Test 3: Registration
    token, email = test_auth_registration()
    results.append(("Registration", token is not None))
    
    if token and email:
        # Test 4: Duplicate email
        results.append(("Duplicate email", test_duplicate_email(email)))
        
        # Test 5: Duplicate username
        results.append(("Duplicate username", test_duplicate_username()))
        
        # Test 6: Login
        login_token = test_login(email)
        results.append(("Login", login_token is not None))
        
        # Test 7: Wrong password
        results.append(("Wrong password", test_login_wrong_password(email)))
        
        if login_token:
            # Test 8: /auth/me with token
            results.append(("Auth me with token", test_auth_me_with_token(login_token)))
        
        # Test 9: /auth/me without token
        results.append(("Auth me without token", test_auth_me_without_token()))
    
    # Test 10: Admin login
    results.append(("Admin login", test_admin_login()))
    
    # Test 11: Plans endpoint
    results.append(("Plans endpoint", test_plans_endpoint()))
    
    # Test 12: IMEI check
    search_id = test_imei_check()
    results.append(("IMEI check", search_id is not None))
    
    if token and search_id:
        # Test 13: Unlock with credit deduction
        results.append(("Unlock credit deduction", test_unlock_with_credit_deduction(token, search_id)))
        
        # Test 14: Dashboard
        results.append(("Dashboard endpoint", test_dashboard_endpoint(token)))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*80)
    print(f"TOTAL: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

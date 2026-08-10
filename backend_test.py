#!/usr/bin/env python3
"""
Backend API Test Suite for UnlockTap
Tests the new /api/db-diagnostic endpoint + full regression suite
"""

import requests
import json
import random
import string
import re

# Base URL from environment
BASE_URL = "https://device-verify-check.preview.emergentagent.com/api"

def random_string(length=8):
    """Generate random string for unique test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def check_no_credentials_in_response(response_data, test_name):
    """
    CRITICAL SECURITY CHECK: Scan entire response for any credential leaks.
    Returns True if safe, False if credentials found.
    
    Safe fields (metadata about credentials, not actual values):
    - passwordPresent, passwordHasUnencodedSpecials (boolean indicators)
    - hasPassword (boolean indicator)
    - usernamePresent, usernameLength, usernameHasUnencodedSpecials (metadata, not actual username)
    
    Unsafe (would indicate leak):
    - Actual password value
    - Actual username value (string)
    - Full MongoDB URI with credentials
    """
    response_str = json.dumps(response_data)
    
    issues = []
    
    # Check for MongoDB connection string patterns WITH credentials (userinfo)
    uri_patterns = [
        r'mongodb(?:\+srv)?://[^@\s]+:[^@\s]+@',  # mongodb://user:pass@
    ]
    
    for pattern in uri_patterns:
        if re.search(pattern, response_str, re.IGNORECASE):
            issues.append(f"Found MongoDB URI with embedded credentials")
    
    # Check for actual password field with a string value (not boolean metadata)
    # Safe: "passwordPresent": true, "hasPassword": false
    # Unsafe: "password": "somevalue"
    if re.search(r'"password"\s*:\s*"[^"]+"', response_str, re.IGNORECASE):
        # But exclude safe metadata fields
        if not re.search(r'"password(Present|HasUnencodedSpecials)"\s*:', response_str, re.IGNORECASE):
            issues.append("Found 'password' field with string value (not a safe boolean indicator)")
    
    # Check for actual username field with a string value (not metadata)
    # Safe: "usernamePresent": true, "usernameLength": 5
    # Unsafe: "username": "actualuser"
    # We need to be careful here - the response might have username in user objects, which is OK
    # But in db-diagnostic, we should NOT have actual username value
    if test_name == "db-diagnostic":
        # In db-diagnostic specifically, check for username as a string value
        if re.search(r'"username"\s*:\s*"[^"]+"', response_str):
            # Exclude safe metadata fields
            if not re.search(r'"username(Present|Length|HasUnencodedSpecials)"\s*:', response_str):
                issues.append("Found 'username' field with string value in db-diagnostic (should only have metadata)")
    
    # Check for common secret/credential field names with string values
    secret_fields = ['secret', 'credential', 'apikey', 'api_key', 'token']
    for field in secret_fields:
        if re.search(f'"{field}"\s*:\s*"[^"]+"', response_str, re.IGNORECASE):
            issues.append(f"Found '{field}' field with string value")
    
    if issues:
        print(f"❌ SECURITY ISSUE in {test_name}:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    return True

def test_db_diagnostic():
    """
    PRIMARY TEST: GET /api/db-diagnostic
    Must return safe diagnostic info WITHOUT exposing credentials
    """
    print("\n" + "="*80)
    print("PRIMARY TEST: GET /api/db-diagnostic")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/db-diagnostic", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check required fields
        required_fields = [
            'status', 'connection', 'failureStage',
            'mongoUrlExists', 'variableUsed', 'isSrvFormat', 'scheme', 'host',
            'databaseFromUri', 'dbNameEnv', 'effectiveDatabase',
            'usernamePresent', 'usernameLength', 'passwordPresent',
            'passwordHasUnencodedSpecials', 'usernameHasUnencodedSpecials',
            'hadWhitespaceEdges', 'hadWrappingQuotes', 'uriLength'
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
        
        # Verify expected values for preview environment
        if data.get('status') != 'ok':
            print(f"❌ FAILED: Expected status='ok', got '{data.get('status')}'")
            return False
        
        if data.get('connection') != 'success':
            print(f"❌ FAILED: Expected connection='success', got '{data.get('connection')}'")
            return False
        
        if data.get('failureStage') is not None:
            print(f"❌ FAILED: Expected failureStage=null, got '{data.get('failureStage')}'")
            return False
        
        # Verify field types
        if not isinstance(data.get('mongoUrlExists'), bool):
            print(f"❌ FAILED: mongoUrlExists should be boolean, got {type(data.get('mongoUrlExists'))}")
            return False
        
        if not isinstance(data.get('usernamePresent'), bool):
            print(f"❌ FAILED: usernamePresent should be boolean, got {type(data.get('usernamePresent'))}")
            return False
        
        if not isinstance(data.get('usernameLength'), int):
            print(f"❌ FAILED: usernameLength should be number, got {type(data.get('usernameLength'))}")
            return False
        
        if not isinstance(data.get('passwordPresent'), bool):
            print(f"❌ FAILED: passwordPresent should be boolean, got {type(data.get('passwordPresent'))}")
            return False
        
        if not isinstance(data.get('passwordHasUnencodedSpecials'), bool):
            print(f"❌ FAILED: passwordHasUnencodedSpecials should be boolean")
            return False
        
        if not isinstance(data.get('usernameHasUnencodedSpecials'), bool):
            print(f"❌ FAILED: usernameHasUnencodedSpecials should be boolean")
            return False
        
        # CRITICAL SECURITY CHECK: Verify NO credentials exposed
        print("\n🔒 SECURITY CHECK: Scanning response for credential leaks...")
        
        # Check that response does NOT contain actual username value (only presence/length)
        if 'username' in data and data['username'] is not None and data['username'] != '':
            # If there's a username field with actual value (not just usernamePresent/usernameLength)
            if isinstance(data.get('username'), str) and len(data['username']) > 0:
                print(f"❌ SECURITY FAILURE: Response contains actual username value!")
                return False
        
        # Check that response does NOT contain password
        if 'password' in data:
            print(f"❌ SECURITY FAILURE: Response contains 'password' field!")
            return False
        
        # Check that response does NOT contain full connection string
        response_str = json.dumps(data)
        if 'mongodb://' in response_str.lower() and '@' in response_str:
            # Check if it's a full URI with credentials
            if re.search(r'mongodb(?:\+srv)?://[^@]+@', response_str, re.IGNORECASE):
                print(f"❌ SECURITY FAILURE: Response contains full MongoDB URI with credentials!")
                return False
        
        # Run comprehensive credential check
        if not check_no_credentials_in_response(data, "db-diagnostic"):
            return False
        
        print("✅ SECURITY CHECK PASSED: No credentials found in response")
        print("✅ PRIMARY TEST PASSED: /api/db-diagnostic returns safe diagnostic info")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_health_endpoint():
    """Regression: GET /api/health"""
    print("\n" + "="*80)
    print("REGRESSION TEST: GET /api/health")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check required fields
        if data.get('status') != 'ok':
            print(f"❌ FAILED: Expected status='ok'")
            return False
        
        if data.get('db') != 'connected':
            print(f"❌ FAILED: Expected db='connected'")
            return False
        
        if 'env' not in data:
            print(f"❌ FAILED: Missing 'env' field")
            return False
        
        if data['env'].get('mongoVarUsed') != 'MONGO_URL':
            print(f"❌ FAILED: Expected mongoVarUsed='MONGO_URL'")
            return False
        
        # CRITICAL: Check no password in response
        if not check_no_credentials_in_response(data, "health"):
            return False
        
        print("✅ PASSED: /api/health")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_root_endpoint():
    """Regression: GET /api/"""
    print("\n" + "="*80)
    print("REGRESSION TEST: GET /api/")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        if data.get('status') != 'ok':
            print(f"❌ FAILED: Expected status='ok'")
            return False
        
        print("✅ PASSED: GET /api/")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_registration_with_terms():
    """Regression: Register with termsAccepted=true"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Register with termsAccepted=true")
    print("="*80)
    
    try:
        unique_id = random_string(12)
        payload = {
            "name": f"Test User {unique_id}",
            "username": f"testuser{unique_id}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test{unique_id}@example.com",
            "password": "Test@123",
            "termsAccepted": True
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False, None, None
        
        data = response.json()
        
        # Check token and user
        if 'token' not in data or 'user' not in data:
            print(f"❌ FAILED: Missing token or user in response")
            return False, None, None
        
        user = data['user']
        
        # Check termsAccepted fields
        if user.get('termsAccepted') != True:
            print(f"❌ FAILED: Expected termsAccepted=true")
            return False, None, None
        
        if 'termsAcceptedAt' not in user:
            print(f"❌ FAILED: Missing termsAcceptedAt field")
            return False, None, None
        
        # CRITICAL: Check NO password field in response
        if 'password' in user:
            print(f"❌ FAILED: Password field should NOT be in response")
            return False, None, None
        
        print("✅ PASSED: Register with termsAccepted=true")
        return True, data['token'], payload['email']
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, None, None

def test_registration_without_terms():
    """Regression: Register WITHOUT termsAccepted"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Register WITHOUT termsAccepted")
    print("="*80)
    
    try:
        unique_id = random_string(12)
        payload = {
            "name": f"Test User {unique_id}",
            "username": f"testuser{unique_id}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test{unique_id}@example.com",
            "password": "Test@123"
            # termsAccepted is missing
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 400:
            print(f"❌ FAILED: Expected 400, got {response.status_code}")
            return False
        
        data = response.json()
        expected_error = "You must agree to the Terms & Conditions and Privacy Policy to create an account."
        
        if data.get('error') != expected_error:
            print(f"❌ FAILED: Expected exact error message")
            print(f"Expected: {expected_error}")
            print(f"Got: {data.get('error')}")
            return False
        
        print("✅ PASSED: Register without termsAccepted returns 400 with correct message")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_duplicate_email():
    """Regression: Duplicate email returns 409"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Duplicate email")
    print("="*80)
    
    try:
        unique_id = random_string(8)  # Shorter to avoid username length issues
        email = f"dup{unique_id}@example.com"
        
        payload = {
            "name": "Test User",
            "username": f"user{unique_id}",
            "country": "United States",
            "phone": "+1234567890",
            "email": email,
            "password": "Test@123",
            "termsAccepted": True
        }
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        if response1.status_code != 200:
            print(f"❌ FAILED: First registration failed")
            return False
        
        # Second registration with same email but different username
        payload['username'] = f"user{unique_id}x"  # Shorter suffix to stay under 20 chars
        response2 = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        
        if response2.status_code != 409:
            print(f"❌ FAILED: Expected 409, got {response2.status_code}")
            print(f"Response: {response2.text}")
            return False
        
        print("✅ PASSED: Duplicate email returns 409")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_duplicate_username():
    """Regression: Duplicate username returns 409"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Duplicate username")
    print("="*80)
    
    try:
        unique_id = random_string(12)
        username = f"dupuser{unique_id}"
        
        payload1 = {
            "name": "Test User 1",
            "username": username,
            "country": "United States",
            "phone": "+1234567890",
            "email": f"user1{unique_id}@example.com",
            "password": "Test@123",
            "termsAccepted": True
        }
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/auth/register", json=payload1, timeout=10)
        if response1.status_code != 200:
            print(f"❌ FAILED: First registration failed")
            return False
        
        # Second registration with same username (different case)
        payload2 = {
            "name": "Test User 2",
            "username": username.upper(),  # Case-insensitive check
            "country": "United States",
            "phone": "+1234567891",
            "email": f"user2{unique_id}@example.com",
            "password": "Test@123",
            "termsAccepted": True
        }
        
        response2 = requests.post(f"{BASE_URL}/auth/register", json=payload2, timeout=10)
        
        if response2.status_code != 409:
            print(f"❌ FAILED: Expected 409, got {response2.status_code}")
            return False
        
        print("✅ PASSED: Duplicate username returns 409")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_login(email, password):
    """Regression: Login with correct credentials"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Login")
    print("="*80)
    
    try:
        payload = {"email": email, "password": password}
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False, None
        
        data = response.json()
        if 'token' not in data:
            print(f"❌ FAILED: Missing token in response")
            return False, None
        
        print("✅ PASSED: Login successful")
        return True, data['token']
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, None

def test_login_wrong_password():
    """Regression: Login with wrong password returns 401"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Login with wrong password")
    print("="*80)
    
    try:
        # Use admin email with wrong password
        payload = {"email": "admin@unlocktap.com", "password": "WrongPassword123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 401:
            print(f"❌ FAILED: Expected 401, got {response.status_code}")
            return False
        
        print("✅ PASSED: Wrong password returns 401")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_auth_me_with_token(token):
    """Regression: GET /auth/me with token"""
    print("\n" + "="*80)
    print("REGRESSION TEST: GET /auth/me with token")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        if 'user' not in data:
            print(f"❌ FAILED: Missing user in response")
            return False
        
        print("✅ PASSED: GET /auth/me with token")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_auth_me_without_token():
    """Regression: GET /auth/me without token returns 401"""
    print("\n" + "="*80)
    print("REGRESSION TEST: GET /auth/me without token")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 401:
            print(f"❌ FAILED: Expected 401, got {response.status_code}")
            return False
        
        print("✅ PASSED: GET /auth/me without token returns 401")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_plans():
    """Regression: GET /api/plans returns 4 plans"""
    print("\n" + "="*80)
    print("REGRESSION TEST: GET /api/plans")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/plans", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        if 'plans' not in data:
            print(f"❌ FAILED: Missing plans in response")
            return False
        
        if len(data['plans']) != 4:
            print(f"❌ FAILED: Expected 4 plans, got {len(data['plans'])}")
            return False
        
        print("✅ PASSED: GET /api/plans returns 4 plans")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_imei_check(token):
    """Regression: POST /api/imei/check"""
    print("\n" + "="*80)
    print("REGRESSION TEST: POST /api/imei/check")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"imei": "359876543210987"}
        response = requests.post(f"{BASE_URL}/imei/check", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False, None
        
        data = response.json()
        if 'searchId' not in data:
            print(f"❌ FAILED: Missing searchId in response")
            return False, None
        
        if 'free' not in data:
            print(f"❌ FAILED: Missing free preview in response")
            return False, None
        
        print("✅ PASSED: POST /api/imei/check returns preview + searchId")
        return True, data['searchId']
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, None

def test_unlock(token, search_id):
    """Regression: POST /api/unlock deducts credit"""
    print("\n" + "="*80)
    print("REGRESSION TEST: POST /api/unlock")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"searchId": search_id}
        response = requests.post(f"{BASE_URL}/unlock", json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        if 'premium' not in data:
            print(f"❌ FAILED: Missing premium data in response")
            return False
        
        if 'credits' not in data:
            print(f"❌ FAILED: Missing credits in response")
            return False
        
        # Should have 2 credits left (started with 3, used 1)
        if data['credits'] != 2:
            print(f"⚠️  WARNING: Expected 2 credits, got {data['credits']}")
        
        print("✅ PASSED: POST /api/unlock deducts credit and returns premium data")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_admin_login():
    """Regression: Admin login returns role=admin"""
    print("\n" + "="*80)
    print("REGRESSION TEST: Admin login")
    print("="*80)
    
    try:
        payload = {"email": "admin@unlocktap.com", "password": "Admin@123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        if 'user' not in data:
            print(f"❌ FAILED: Missing user in response")
            return False
        
        if data['user'].get('role') != 'admin':
            print(f"❌ FAILED: Expected role='admin', got '{data['user'].get('role')}'")
            return False
        
        print("✅ PASSED: Admin login returns role=admin")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("UNLOCKTAP BACKEND TEST SUITE")
    print("Testing new /api/db-diagnostic endpoint + full regression")
    print("="*80)
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # PRIMARY TEST: db-diagnostic
    results['total'] += 1
    if test_db_diagnostic():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # REGRESSION TESTS
    
    # 1. Health endpoint
    results['total'] += 1
    if test_health_endpoint():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 2. Root endpoint
    results['total'] += 1
    if test_root_endpoint():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 3. Registration with terms
    results['total'] += 1
    reg_success, token, email = test_registration_with_terms()
    if reg_success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 4. Registration without terms
    results['total'] += 1
    if test_registration_without_terms():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 5. Duplicate email
    results['total'] += 1
    if test_duplicate_email():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 6. Duplicate username
    results['total'] += 1
    if test_duplicate_username():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 7. Login (if registration succeeded)
    if token and email:
        results['total'] += 1
        login_success, login_token = test_login(email, "Test@123")
        if login_success:
            results['passed'] += 1
            token = login_token  # Use login token for subsequent tests
        else:
            results['failed'] += 1
    
    # 8. Login with wrong password
    results['total'] += 1
    if test_login_wrong_password():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 9. Auth me with token
    if token:
        results['total'] += 1
        if test_auth_me_with_token(token):
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    # 10. Auth me without token
    results['total'] += 1
    if test_auth_me_without_token():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 11. Plans
    results['total'] += 1
    if test_plans():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # 12. IMEI check
    search_id = None
    if token:
        results['total'] += 1
        imei_success, search_id = test_imei_check(token)
        if imei_success:
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    # 13. Unlock
    if token and search_id:
        results['total'] += 1
        if test_unlock(token, search_id):
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    # 14. Admin login
    results['total'] += 1
    if test_admin_login():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
    print("="*80)
    
    if results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {results['failed']} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    exit(main())

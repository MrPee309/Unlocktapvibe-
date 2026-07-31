#!/usr/bin/env python3
"""
UnlockTap Backend Testing - Updated Customer Registration Flow
Tests the expanded registration form with name, username, country, phone, email, password
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Base URL from environment
BASE_URL = "https://device-verify-check.preview.emergentagent.com/api"

# Test results storage
test_results = []

def log_test(test_name: str, passed: bool, details: str = "", response_data: Any = None):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = {
        "test": test_name,
        "status": status,
        "passed": passed,
        "details": details,
        "response": response_data
    }
    test_results.append(result)
    print(f"{status} | {test_name}")
    if details:
        print(f"    Details: {details}")
    if not passed and response_data:
        print(f"    Response: {json.dumps(response_data, indent=2)}")
    print()

# ============================================================================
# TEST GROUP 1: REGISTRATION WITH NEW FIELDS
# ============================================================================

def test_register_valid_full():
    """Test 1.1: Valid registration with ALL 6 fields"""
    test_name = "POST /api/auth/register - Valid full registration (all 6 fields)"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "John Smith",
            "username": f"johnsmith{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"john.smith.{timestamp}@example.com",
            "password": "SecurePass123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code != 200:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
            return None
        
        # Check token exists
        if "token" not in data:
            log_test(test_name, False, "Token not returned", data)
            return None
        
        # Check user object
        if "user" not in data:
            log_test(test_name, False, "User object not returned", data)
            return None
        
        user = data["user"]
        
        # Verify all profile fields are present
        required_fields = ["name", "username", "country", "phone", "email"]
        missing_fields = [f for f in required_fields if f not in user]
        if missing_fields:
            log_test(test_name, False, f"Missing fields in response: {missing_fields}", data)
            return None
        
        # Verify credits = 3
        if user.get("credits") != 3:
            log_test(test_name, False, f"Expected 3 credits, got {user.get('credits')}", data)
            return None
        
        # Verify role = user
        if user.get("role") != "user":
            log_test(test_name, False, f"Expected role='user', got {user.get('role')}", data)
            return None
        
        # Verify NO password field in response
        if "password" in user:
            log_test(test_name, False, "Password field present in response (SECURITY ISSUE)", data)
            return None
        
        log_test(test_name, True, f"User registered successfully with all fields, 3 credits, role=user, no password in response")
        return {
            "email": payload["email"],
            "username": payload["username"],
            "password": payload["password"],
            "token": data["token"],
            "user": user
        }
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return None

def test_register_missing_name():
    """Test 1.2: Missing name field"""
    test_name = "POST /api/auth/register - Missing name"
    try:
        timestamp = int(time.time())
        payload = {
            # "name": missing
            "username": f"user{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing name")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_missing_username():
    """Test 1.3: Missing username field"""
    test_name = "POST /api/auth/register - Missing username"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            # "username": missing
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing username")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_missing_country():
    """Test 1.4: Missing country field"""
    test_name = "POST /api/auth/register - Missing country"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            # "country": missing
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing country")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_missing_phone():
    """Test 1.5: Missing phone field"""
    test_name = "POST /api/auth/register - Missing phone"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            "country": "United States",
            # "phone": missing
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing phone")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_missing_email():
    """Test 1.6: Missing email field"""
    test_name = "POST /api/auth/register - Missing email"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            # "email": missing
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing email")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_missing_password():
    """Test 1.7: Missing password field"""
    test_name = "POST /api/auth/register - Missing password"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            # "password": missing
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing password")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_invalid_username_too_short():
    """Test 1.8: Invalid username - too short (< 3 chars)"""
    test_name = "POST /api/auth/register - Invalid username (too short: 'ab')"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": "ab",  # Only 2 chars
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for username < 3 chars")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_invalid_username_with_space():
    """Test 1.9: Invalid username - contains space"""
    test_name = "POST /api/auth/register - Invalid username (contains space)"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": "has space",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for username with space")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_invalid_username_too_long():
    """Test 1.10: Invalid username - too long (> 20 chars)"""
    test_name = "POST /api/auth/register - Invalid username (too long: >20 chars)"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": "toolongusernameover20chars_x",  # 28 chars
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for username > 20 chars")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_invalid_phone():
    """Test 1.11: Invalid phone format"""
    test_name = "POST /api/auth/register - Invalid phone (non-numeric)"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            "country": "United States",
            "phone": "abc",  # Invalid
            "email": f"test.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for invalid phone")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_short_password():
    """Test 1.12: Password < 6 characters"""
    test_name = "POST /api/auth/register - Password < 6 chars"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            "email": f"test.{timestamp}@example.com",
            "password": "12345"  # Only 5 chars
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for password < 6 chars")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_invalid_email():
    """Test 1.13: Invalid email format"""
    test_name = "POST /api/auth/register - Invalid email format"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Test User",
            "username": f"user{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            "email": "invalid-email-format",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for invalid email")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_duplicate_email(email: str):
    """Test 1.14: Duplicate email"""
    test_name = "POST /api/auth/register - Duplicate email"
    try:
        timestamp = int(time.time())
        payload = {
            "name": "Duplicate User",
            "username": f"duplicate{timestamp}",
            "country": "United States",
            "phone": "+1234567890",
            "email": email,  # Duplicate
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 409:
            log_test(test_name, True, "Correctly returned 409 for duplicate email")
        else:
            log_test(test_name, False, f"Expected 409, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_duplicate_username_case_insensitive(username: str):
    """Test 1.15: Duplicate username (case-insensitive)"""
    test_name = "POST /api/auth/register - Duplicate username (case-insensitive)"
    try:
        timestamp = int(time.time())
        # Try to register with same username but different case
        duplicate_username = username.lower() if username.isupper() else username.upper()
        
        payload = {
            "name": "Duplicate Username User",
            "username": duplicate_username,  # Same username, different case
            "country": "United States",
            "phone": "+1987654321",
            "email": f"different.{timestamp}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 409:
            log_test(test_name, True, f"Correctly returned 409 for duplicate username (tried '{duplicate_username}' when '{username}' exists)")
        else:
            log_test(test_name, False, f"Expected 409, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

# ============================================================================
# TEST GROUP 2: LOGIN (unchanged, email-based)
# ============================================================================

def test_login_valid(email: str, password: str):
    """Test 2.1: Valid login with email and password"""
    test_name = "POST /api/auth/login - Valid credentials"
    try:
        payload = {
            "email": email,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        data = response.json()
        
        if response.status_code == 200:
            if "token" in data and "user" in data:
                log_test(test_name, True, "Login successful with token and user")
                return data["token"]
            else:
                log_test(test_name, False, "Token or user missing in response", data)
                return None
        else:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
            return None
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST GROUP 3: AUTH/ME WITH TOKEN
# ============================================================================

def test_auth_me_with_token(token: str):
    """Test 3.1: GET /api/auth/me with valid Bearer token"""
    test_name = "GET /api/auth/me - With valid Bearer token"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            if "user" in data:
                user = data["user"]
                # Verify profile fields are present
                required_fields = ["name", "username", "country", "phone", "email"]
                missing_fields = [f for f in required_fields if f not in user]
                if missing_fields:
                    log_test(test_name, False, f"Missing fields in /auth/me response: {missing_fields}", data)
                    return False
                
                # Verify no password field
                if "password" in user:
                    log_test(test_name, False, "Password field present in /auth/me response (SECURITY ISSUE)", data)
                    return False
                
                log_test(test_name, True, "Successfully retrieved user with all profile fields, no password")
                return True
            else:
                log_test(test_name, False, "User object missing in response", data)
                return False
        else:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
            return False
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return False

# ============================================================================
# TEST GROUP 4: PROTECTED ENDPOINTS ACCESS
# ============================================================================

def test_protected_endpoints_with_token(token: str):
    """Test 4: Access protected endpoints with token"""
    endpoints = [
        "/dashboard",
        "/history",
        "/reports",
        "/orders"
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for endpoint in endpoints:
        test_name = f"GET /api{endpoint} - With Bearer token"
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            data = response.json()
            
            if response.status_code == 200:
                log_test(test_name, True, "Successfully accessed protected endpoint")
            else:
                log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
        except Exception as e:
            log_test(test_name, False, f"Exception: {str(e)}")

def test_protected_endpoints_without_token():
    """Test 5: Access protected endpoints without token"""
    endpoints = [
        "/dashboard",
        "/history",
        "/reports",
        "/orders"
    ]
    
    for endpoint in endpoints:
        test_name = f"GET /api{endpoint} - Without token"
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            data = response.json()
            
            if response.status_code == 401:
                log_test(test_name, True, "Correctly returned 401 without token")
            else:
                log_test(test_name, False, f"Expected 401, got {response.status_code}", data)
        except Exception as e:
            log_test(test_name, False, f"Exception: {str(e)}")

# ============================================================================
# TEST GROUP 6: DATA ISOLATION
# ============================================================================

def test_data_isolation():
    """Test 6: Complete data isolation flow"""
    print("\n--- STARTING DATA ISOLATION TEST ---")
    
    # Step 1: Register User A
    timestamp_a = int(time.time())
    user_a_payload = {
        "name": "Alice Johnson",
        "username": f"alice{timestamp_a}",
        "country": "United States",
        "phone": "+1111111111",
        "email": f"alice.{timestamp_a}@example.com",
        "password": "alicepass123"
    }
    
    test_name = "Data Isolation - Register User A"
    try:
        response_a = requests.post(f"{BASE_URL}/auth/register", json=user_a_payload)
        data_a = response_a.json()
        
        if response_a.status_code != 200 or "token" not in data_a:
            log_test(test_name, False, "Failed to register User A", data_a)
            return
        
        token_a = data_a["token"]
        log_test(test_name, True, "User A registered successfully")
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 2: User A performs IMEI check
    test_name = "Data Isolation - User A IMEI check"
    try:
        imei_payload = {"imei": "123456789012345"}
        headers_a = {"Authorization": f"Bearer {token_a}"}
        response_imei = requests.post(f"{BASE_URL}/imei/check", json=imei_payload, headers=headers_a)
        data_imei = response_imei.json()
        
        if response_imei.status_code != 200 or "searchId" not in data_imei:
            log_test(test_name, False, "Failed IMEI check for User A", data_imei)
            return
        
        search_id_a = data_imei["searchId"]
        log_test(test_name, True, f"User A IMEI check successful, searchId: {search_id_a}")
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 3: User A unlocks report (spends 1 credit)
    test_name = "Data Isolation - User A unlock report"
    try:
        unlock_payload = {"searchId": search_id_a}
        response_unlock = requests.post(f"{BASE_URL}/unlock", json=unlock_payload, headers=headers_a)
        data_unlock = response_unlock.json()
        
        if response_unlock.status_code != 200:
            log_test(test_name, False, "Failed to unlock report for User A", data_unlock)
            return
        
        # Verify credits decreased to 2
        if data_unlock.get("credits") != 2:
            log_test(test_name, False, f"Expected 2 credits after unlock, got {data_unlock.get('credits')}", data_unlock)
            return
        
        log_test(test_name, True, "User A unlocked report, credits decreased to 2")
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 4: Register User B
    time.sleep(1)  # Ensure different timestamp
    timestamp_b = int(time.time())
    user_b_payload = {
        "name": "Bob Williams",
        "username": f"bob{timestamp_b}",
        "country": "Canada",
        "phone": "+2222222222",
        "email": f"bob.{timestamp_b}@example.com",
        "password": "bobpass123"
    }
    
    test_name = "Data Isolation - Register User B"
    try:
        response_b = requests.post(f"{BASE_URL}/auth/register", json=user_b_payload)
        data_b = response_b.json()
        
        if response_b.status_code != 200 or "token" not in data_b:
            log_test(test_name, False, "Failed to register User B", data_b)
            return
        
        token_b = data_b["token"]
        log_test(test_name, True, "User B registered successfully")
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 5: User B login
    test_name = "Data Isolation - User B login"
    try:
        login_b_payload = {"email": user_b_payload["email"], "password": user_b_payload["password"]}
        response_login_b = requests.post(f"{BASE_URL}/auth/login", json=login_b_payload)
        data_login_b = response_login_b.json()
        
        if response_login_b.status_code != 200:
            log_test(test_name, False, "Failed to login User B", data_login_b)
            return
        
        log_test(test_name, True, "User B login successful")
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 6: User B checks history (should be EMPTY)
    test_name = "Data Isolation - User B history (should be empty)"
    try:
        headers_b = {"Authorization": f"Bearer {token_b}"}
        response_history_b = requests.get(f"{BASE_URL}/history", headers=headers_b)
        data_history_b = response_history_b.json()
        
        if response_history_b.status_code != 200:
            log_test(test_name, False, "Failed to get User B history", data_history_b)
            return
        
        items_b = data_history_b.get("items", [])
        if len(items_b) == 0:
            log_test(test_name, True, "User B history is empty (correct isolation)")
        else:
            log_test(test_name, False, f"User B history should be empty but contains {len(items_b)} items (DATA LEAK)", data_history_b)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 7: User B checks reports (should be EMPTY)
    test_name = "Data Isolation - User B reports (should be empty)"
    try:
        response_reports_b = requests.get(f"{BASE_URL}/reports", headers=headers_b)
        data_reports_b = response_reports_b.json()
        
        if response_reports_b.status_code != 200:
            log_test(test_name, False, "Failed to get User B reports", data_reports_b)
            return
        
        items_b = data_reports_b.get("items", [])
        if len(items_b) == 0:
            log_test(test_name, True, "User B reports are empty (correct isolation)")
        else:
            log_test(test_name, False, f"User B reports should be empty but contains {len(items_b)} items (DATA LEAK)", data_reports_b)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 8: User A checks history (should contain 1 search)
    test_name = "Data Isolation - User A history (should contain search)"
    try:
        response_history_a = requests.get(f"{BASE_URL}/history", headers=headers_a)
        data_history_a = response_history_a.json()
        
        if response_history_a.status_code != 200:
            log_test(test_name, False, "Failed to get User A history", data_history_a)
            return
        
        items_a = data_history_a.get("items", [])
        if len(items_a) >= 1:
            log_test(test_name, True, f"User A history contains {len(items_a)} search(es)")
        else:
            log_test(test_name, False, "User A history should contain at least 1 search", data_history_a)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 9: User A checks reports (should contain 1 report)
    test_name = "Data Isolation - User A reports (should contain report)"
    try:
        response_reports_a = requests.get(f"{BASE_URL}/reports", headers=headers_a)
        data_reports_a = response_reports_a.json()
        
        if response_reports_a.status_code != 200:
            log_test(test_name, False, "Failed to get User A reports", data_reports_a)
            return
        
        items_a = data_reports_a.get("items", [])
        if len(items_a) >= 1:
            log_test(test_name, True, f"User A reports contain {len(items_a)} report(s)")
        else:
            log_test(test_name, False, "User A reports should contain at least 1 report", data_reports_a)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 10: User A purchases credits (checkout)
    test_name = "Data Isolation - User A checkout (buy credits)"
    try:
        checkout_payload = {"planId": "starter"}
        response_checkout = requests.post(f"{BASE_URL}/checkout", json=checkout_payload, headers=headers_a)
        data_checkout = response_checkout.json()
        
        if response_checkout.status_code != 200:
            log_test(test_name, False, "Failed checkout for User A", data_checkout)
            return
        
        # User A should now have 2 + 10 = 12 credits
        if data_checkout.get("credits") != 12:
            log_test(test_name, False, f"Expected 12 credits after checkout, got {data_checkout.get('credits')}", data_checkout)
            return
        
        log_test(test_name, True, "User A checkout successful, credits increased to 12")
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 11: User B checks orders (should be EMPTY)
    test_name = "Data Isolation - User B orders (should be empty)"
    try:
        response_orders_b = requests.get(f"{BASE_URL}/orders", headers=headers_b)
        data_orders_b = response_orders_b.json()
        
        if response_orders_b.status_code != 200:
            log_test(test_name, False, "Failed to get User B orders", data_orders_b)
            return
        
        items_b = data_orders_b.get("items", [])
        if len(items_b) == 0:
            log_test(test_name, True, "User B orders are empty (correct isolation)")
        else:
            log_test(test_name, False, f"User B orders should be empty but contains {len(items_b)} items (DATA LEAK)", data_orders_b)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return
    
    # Step 12: User A checks orders (should contain 1 order)
    test_name = "Data Isolation - User A orders (should contain order)"
    try:
        response_orders_a = requests.get(f"{BASE_URL}/orders", headers=headers_a)
        data_orders_a = response_orders_a.json()
        
        if response_orders_a.status_code != 200:
            log_test(test_name, False, "Failed to get User A orders", data_orders_a)
            return
        
        items_a = data_orders_a.get("items", [])
        if len(items_a) >= 1:
            log_test(test_name, True, f"User A orders contain {len(items_a)} order(s)")
        else:
            log_test(test_name, False, "User A orders should contain at least 1 order", data_orders_a)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return

# ============================================================================
# TEST GROUP 7: ADMIN LOGIN
# ============================================================================

def test_admin_login():
    """Test 7: Admin login still works"""
    test_name = "POST /api/auth/login - Admin credentials"
    try:
        payload = {
            "email": "admin@unlocktap.com",
            "password": "Admin@123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        data = response.json()
        
        if response.status_code == 200:
            if "user" in data and data["user"].get("role") == "admin":
                log_test(test_name, True, "Admin login successful with role='admin'")
                return data["token"]
            else:
                log_test(test_name, False, f"Expected role='admin', got {data.get('user', {}).get('role')}", data)
                return None
        else:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
            return None
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return None

# ============================================================================
# SUMMARY
# ============================================================================

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("UNLOCKTAP BACKEND TESTING SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    print("-"*80)
    print(f"{'TEST NAME':<70} {'STATUS':<10}")
    print("-"*80)
    
    for result in test_results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        test_name = result['test'][:68]
        print(f"{test_name:<70} {status:<10}")
    
    print("-"*80)
    
    # Print failed tests details
    failed_tests = [r for r in test_results if not r["passed"]]
    if failed_tests:
        print("\n" + "="*80)
        print("FAILED TESTS DETAILS")
        print("="*80)
        for result in failed_tests:
            print(f"\n❌ {result['test']}")
            print(f"   Details: {result['details']}")
            if result['response']:
                print(f"   Response: {json.dumps(result['response'], indent=2)}")
    
    print("\n" + "="*80)

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    print("="*80)
    print("UNLOCKTAP BACKEND TESTING - UPDATED CUSTOMER REGISTRATION FLOW")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    print()
    
    # Test Group 1: Registration with new fields
    print("--- TEST GROUP 1: REGISTRATION (6 FIELDS) ---")
    user_data = test_register_valid_full()
    
    # Test missing fields
    test_register_missing_name()
    test_register_missing_username()
    test_register_missing_country()
    test_register_missing_phone()
    test_register_missing_email()
    test_register_missing_password()
    
    # Test invalid username formats
    test_register_invalid_username_too_short()
    test_register_invalid_username_with_space()
    test_register_invalid_username_too_long()
    
    # Test invalid phone
    test_register_invalid_phone()
    
    # Test short password
    test_register_short_password()
    
    # Test invalid email
    test_register_invalid_email()
    
    # Test duplicates
    if user_data:
        test_register_duplicate_email(user_data["email"])
        test_register_duplicate_username_case_insensitive(user_data["username"])
    
    print()
    
    # Test Group 2: Login
    print("--- TEST GROUP 2: LOGIN ---")
    user_token = None
    if user_data:
        user_token = test_login_valid(user_data["email"], user_data["password"])
    print()
    
    # Test Group 3: Auth/me
    print("--- TEST GROUP 3: GET /auth/me ---")
    if user_token:
        test_auth_me_with_token(user_token)
    print()
    
    # Test Group 4: Protected endpoints with token
    print("--- TEST GROUP 4: PROTECTED ENDPOINTS (WITH TOKEN) ---")
    if user_token:
        test_protected_endpoints_with_token(user_token)
    print()
    
    # Test Group 5: Protected endpoints without token
    print("--- TEST GROUP 5: PROTECTED ENDPOINTS (WITHOUT TOKEN) ---")
    test_protected_endpoints_without_token()
    print()
    
    # Test Group 6: Data isolation
    print("--- TEST GROUP 6: DATA ISOLATION ---")
    test_data_isolation()
    print()
    
    # Test Group 7: Admin login
    print("--- TEST GROUP 7: ADMIN LOGIN ---")
    test_admin_login()
    print()
    
    # Print summary
    print_summary()
    
    # Return exit code
    failed = sum(1 for r in test_results if not r["passed"])
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())

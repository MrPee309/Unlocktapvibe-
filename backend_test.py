#!/usr/bin/env python3
"""
Focused Auth-Only Verification for UnlockTap
Tests all authentication endpoints with comprehensive scenarios
"""

import requests
import json
import base64
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

def decode_token_payload(token: str) -> Optional[Dict]:
    """Decode JWT-like token payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        
        # Decode base64url
        data = parts[0]
        # Add padding if needed
        data += '=' * (4 - len(data) % 4)
        data = data.replace('-', '+').replace('_', '/')
        
        decoded = base64.b64decode(data)
        payload = json.loads(decoded)
        return payload
    except Exception as e:
        print(f"Token decode error: {e}")
        return None

def test_register_valid():
    """Test 1.1: Valid registration"""
    test_name = "POST /api/auth/register - Valid registration"
    try:
        payload = {
            "name": "Test User",
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 200:
            # Check token exists
            if "token" not in data:
                log_test(test_name, False, "Token not returned", data)
                return None
            
            # Check user object
            if "user" not in data:
                log_test(test_name, False, "User object not returned", data)
                return None
            
            user = data["user"]
            
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
                log_test(test_name, False, "Password field present in response (security issue)", data)
                return None
            
            log_test(test_name, True, f"User registered with 3 credits, role=user, no password in response")
            return {"email": payload["email"], "password": payload["password"], "token": data["token"], "user": user}
        else:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
            return None
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return None

def test_register_duplicate(email: str):
    """Test 1.2: Duplicate email registration"""
    test_name = "POST /api/auth/register - Duplicate email"
    try:
        payload = {
            "name": "Duplicate User",
            "email": email,
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

def test_register_invalid_email():
    """Test 1.3: Invalid email format"""
    test_name = "POST /api/auth/register - Invalid email format"
    try:
        payload = {
            "name": "Test User",
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

def test_register_short_password():
    """Test 1.4: Password < 6 characters"""
    test_name = "POST /api/auth/register - Password < 6 chars"
    try:
        payload = {
            "name": "Test User",
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "12345"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for short password")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_register_missing_fields():
    """Test 1.5: Missing required fields"""
    test_name = "POST /api/auth/register - Missing fields"
    try:
        payload = {
            "name": "Test User",
            "email": f"testuser_{int(time.time())}@example.com"
            # Missing password
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing fields")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_login_valid(email: str, password: str):
    """Test 2.1: Valid login"""
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

def test_login_wrong_password(email: str):
    """Test 2.2: Wrong password"""
    test_name = "POST /api/auth/login - Wrong password"
    try:
        payload = {
            "email": email,
            "password": "wrongpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        data = response.json()
        
        if response.status_code == 401:
            log_test(test_name, True, "Correctly returned 401 for wrong password")
        else:
            log_test(test_name, False, f"Expected 401, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_login_nonexistent_email():
    """Test 2.3: Non-existent email"""
    test_name = "POST /api/auth/login - Non-existent email"
    try:
        payload = {
            "email": f"nonexistent_{int(time.time())}@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        data = response.json()
        
        if response.status_code == 401:
            log_test(test_name, True, "Correctly returned 401 for non-existent email")
        else:
            log_test(test_name, False, f"Expected 401, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_login_missing_fields():
    """Test 2.4: Missing fields"""
    test_name = "POST /api/auth/login - Missing fields"
    try:
        payload = {
            "email": "test@example.com"
            # Missing password
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for missing fields")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_admin_login():
    """Test 3: Admin login"""
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

def test_auth_me_with_token(token: str):
    """Test 4.1: GET /api/auth/me with valid token"""
    test_name = "GET /api/auth/me - With valid Bearer token"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            if "user" in data:
                log_test(test_name, True, "Successfully retrieved user with valid token")
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

def test_auth_me_without_token():
    """Test 4.2: GET /api/auth/me without token"""
    test_name = "GET /api/auth/me - Without token"
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        data = response.json()
        
        if response.status_code == 401:
            log_test(test_name, True, "Correctly returned 401 without token")
        else:
            log_test(test_name, False, f"Expected 401, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_auth_me_malformed_token():
    """Test 4.3: GET /api/auth/me with malformed token"""
    test_name = "GET /api/auth/me - With malformed token"
    try:
        headers = {"Authorization": "Bearer invalid_token_format"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        data = response.json()
        
        if response.status_code == 401:
            log_test(test_name, True, "Correctly returned 401 for malformed token")
        else:
            log_test(test_name, False, f"Expected 401, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_auth_me_tampered_token(token: str):
    """Test 4.4: GET /api/auth/me with tampered token"""
    test_name = "GET /api/auth/me - With tampered token (HMAC verification)"
    try:
        # Tamper with the token by changing a character in the data part
        if len(token) > 10:
            tampered = token[0] + ('X' if token[1] != 'X' else 'Y') + token[2:]
        else:
            tampered = "tampered.token"
        
        headers = {"Authorization": f"Bearer {tampered}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        data = response.json()
        
        if response.status_code == 401:
            log_test(test_name, True, "Correctly returned 401 for tampered token (HMAC signature verification working)")
        else:
            log_test(test_name, False, f"Expected 401, got {response.status_code} - SECURITY ISSUE: tampered token accepted!", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_forgot_password_existing_email(email: str):
    """Test 5.1: Forgot password with existing email"""
    test_name = "POST /api/auth/forgot-password - Existing email"
    try:
        payload = {"email": email}
        response = requests.post(f"{BASE_URL}/auth/forgot-password", json=payload)
        data = response.json()
        
        if response.status_code == 200:
            if "demoResetCode" in data and data["demoResetCode"]:
                log_test(test_name, True, f"Reset code returned: {data['demoResetCode']}")
                return data["demoResetCode"]
            else:
                log_test(test_name, False, "demoResetCode not present or null", data)
                return None
        else:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
            return None
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")
        return None

def test_forgot_password_nonexistent_email():
    """Test 5.2: Forgot password with non-existent email"""
    test_name = "POST /api/auth/forgot-password - Non-existent email"
    try:
        payload = {"email": f"nonexistent_{int(time.time())}@example.com"}
        response = requests.post(f"{BASE_URL}/auth/forgot-password", json=payload)
        data = response.json()
        
        if response.status_code == 200:
            # Should return 200 with generic message, no code or null code
            if data.get("demoResetCode") is None:
                log_test(test_name, True, "Correctly returned 200 with null code for non-existent email")
            else:
                log_test(test_name, False, f"Expected null code, got: {data.get('demoResetCode')}", data)
        else:
            log_test(test_name, False, f"Expected 200, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_reset_password_flow():
    """Test 6: Complete reset password flow"""
    test_name_base = "POST /api/auth/reset-password - Full flow"
    
    # Step 1: Register a new user
    try:
        email = f"resettest_{int(time.time())}@example.com"
        old_password = "oldpassword123"
        new_password = "newpassword456"
        
        # Register
        reg_payload = {
            "name": "Reset Test User",
            "email": email,
            "password": old_password
        }
        reg_response = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        if reg_response.status_code != 200:
            log_test(f"{test_name_base} - Registration", False, f"Failed to register user: {reg_response.status_code}")
            return
        
        # Step 2: Request forgot password
        forgot_payload = {"email": email}
        forgot_response = requests.post(f"{BASE_URL}/auth/forgot-password", json=forgot_payload)
        forgot_data = forgot_response.json()
        
        if forgot_response.status_code != 200 or not forgot_data.get("demoResetCode"):
            log_test(f"{test_name_base} - Forgot password", False, "Failed to get reset code", forgot_data)
            return
        
        reset_code = forgot_data["demoResetCode"]
        
        # Step 3: Reset password
        reset_payload = {
            "email": email,
            "code": reset_code,
            "password": new_password
        }
        reset_response = requests.post(f"{BASE_URL}/auth/reset-password", json=reset_payload)
        
        if reset_response.status_code != 200:
            log_test(f"{test_name_base} - Reset password", False, f"Expected 200, got {reset_response.status_code}", reset_response.json())
            return
        
        log_test(f"{test_name_base} - Reset password", True, "Password reset successful")
        
        # Step 4: Login with NEW password
        login_new_payload = {"email": email, "password": new_password}
        login_new_response = requests.post(f"{BASE_URL}/auth/login", json=login_new_payload)
        
        if login_new_response.status_code != 200:
            log_test(f"{test_name_base} - Login with NEW password", False, f"Expected 200, got {login_new_response.status_code}", login_new_response.json())
            return
        
        log_test(f"{test_name_base} - Login with NEW password", True, "Login successful with new password")
        
        # Step 5: Login with OLD password (should fail)
        login_old_payload = {"email": email, "password": old_password}
        login_old_response = requests.post(f"{BASE_URL}/auth/login", json=login_old_payload)
        
        if login_old_response.status_code == 401:
            log_test(f"{test_name_base} - Login with OLD password", True, "Correctly rejected old password (401)")
        else:
            log_test(f"{test_name_base} - Login with OLD password", False, f"Expected 401, got {login_old_response.status_code} - SECURITY ISSUE: old password still works!", login_old_response.json())
        
    except Exception as e:
        log_test(f"{test_name_base} - Exception", False, f"Exception: {str(e)}")

def test_reset_password_wrong_code(email: str):
    """Test 6.2: Reset password with wrong code"""
    test_name = "POST /api/auth/reset-password - Wrong/invalid reset code"
    try:
        payload = {
            "email": email,
            "code": "WRONGCODE",
            "password": "newpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/reset-password", json=payload)
        data = response.json()
        
        if response.status_code == 400:
            log_test(test_name, True, "Correctly returned 400 for invalid reset code")
        else:
            log_test(test_name, False, f"Expected 400, got {response.status_code}", data)
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def test_token_structure_and_persistence(token: str):
    """Test 7: Token structure and session persistence"""
    test_name = "Token structure verification (sub, role, exp)"
    
    try:
        payload = decode_token_payload(token)
        
        if not payload:
            log_test(test_name, False, "Failed to decode token payload")
            return
        
        # Check for required fields
        required_fields = ["sub", "role", "exp"]
        missing_fields = [f for f in required_fields if f not in payload]
        
        if missing_fields:
            log_test(test_name, False, f"Missing required fields: {missing_fields}", payload)
            return
        
        log_test(test_name, True, f"Token contains sub={payload['sub']}, role={payload['role']}, exp={payload['exp']}")
        
        # Test session persistence - multiple calls with same token
        test_name_persistence = "Session persistence - Multiple /auth/me calls"
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Make 3 consecutive calls
            responses = []
            for i in range(3):
                response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                responses.append(response.status_code)
                time.sleep(0.1)
            
            if all(status == 200 for status in responses):
                log_test(test_name_persistence, True, "Token works consistently across multiple calls")
            else:
                log_test(test_name_persistence, False, f"Inconsistent responses: {responses}")
        except Exception as e:
            log_test(test_name_persistence, False, f"Exception: {str(e)}")
            
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}")

def print_summary():
    """Print test summary table"""
    print("\n" + "="*80)
    print("AUTH TESTING SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    print("-"*80)
    print(f"{'TEST NAME':<60} {'STATUS':<10}")
    print("-"*80)
    
    for result in test_results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{result['test']:<60} {status:<10}")
    
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

def main():
    """Run all auth tests"""
    print("="*80)
    print("UNLOCKTAP AUTH-ONLY VERIFICATION")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    print()
    
    # Test 1: Registration
    print("--- TEST GROUP 1: REGISTRATION ---")
    user_data = test_register_valid()
    if user_data:
        test_register_duplicate(user_data["email"])
    test_register_invalid_email()
    test_register_short_password()
    test_register_missing_fields()
    print()
    
    # Test 2: Login
    print("--- TEST GROUP 2: LOGIN ---")
    if user_data:
        user_token = test_login_valid(user_data["email"], user_data["password"])
        test_login_wrong_password(user_data["email"])
    test_login_nonexistent_email()
    test_login_missing_fields()
    print()
    
    # Test 3: Admin login
    print("--- TEST GROUP 3: ADMIN LOGIN ---")
    admin_token = test_admin_login()
    print()
    
    # Test 4: /auth/me endpoint
    print("--- TEST GROUP 4: GET /auth/me ---")
    if user_token:
        test_auth_me_with_token(user_token)
        test_auth_me_tampered_token(user_token)
    test_auth_me_without_token()
    test_auth_me_malformed_token()
    print()
    
    # Test 5: Forgot password
    print("--- TEST GROUP 5: FORGOT PASSWORD ---")
    if user_data:
        reset_code = test_forgot_password_existing_email(user_data["email"])
    test_forgot_password_nonexistent_email()
    print()
    
    # Test 6: Reset password
    print("--- TEST GROUP 6: RESET PASSWORD ---")
    test_reset_password_flow()
    if user_data:
        test_reset_password_wrong_code(user_data["email"])
    print()
    
    # Test 7: Token structure and persistence
    print("--- TEST GROUP 7: TOKEN STRUCTURE & SESSION PERSISTENCE ---")
    if user_token:
        test_token_structure_and_persistence(user_token)
    print()
    
    # Print summary
    print_summary()
    
    # Return exit code
    failed = sum(1 for r in test_results if not r["passed"])
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())

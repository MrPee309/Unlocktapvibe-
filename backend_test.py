#!/usr/bin/env python3
"""
UnlockTap Backend API Test Suite
Tests all backend endpoints for the UnlockTap application
"""

import requests
import json
import sys
from typing import Dict, Optional

# Base URL from environment
BASE_URL = "https://device-verify-check.preview.emergentagent.com/api"

# Test data
TEST_USER = {
    "name": "John Smith",
    "email": f"testuser_{hash('test')}@example.com",
    "password": "SecurePass123"
}

ADMIN_CREDS = {
    "email": "admin@unlocktap.com",
    "password": "Admin@123"
}

TEST_IMEI = "359876543210987"
TEST_SERIAL = "C39XY0ABJCLF"

# Global state
user_token = None
admin_token = None
search_id_imei = None
search_id_serial = None

def print_test(name: str):
    """Print test name"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_success(msg: str):
    """Print success message"""
    print(f"✅ {msg}")

def print_error(msg: str):
    """Print error message"""
    print(f"❌ {msg}")

def make_request(method: str, endpoint: str, token: Optional[str] = None, 
                 data: Optional[Dict] = None, expected_status: int = 200) -> tuple:
    """Make HTTP request and return (success, response, data)"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return False, None, {"error": f"Unknown method {method}"}
        
        try:
            response_data = resp.json()
        except:
            response_data = {"text": resp.text}
        
        if resp.status_code != expected_status:
            print_error(f"Expected status {expected_status}, got {resp.status_code}")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return False, resp, response_data
        
        return True, resp, response_data
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False, None, {"error": str(e)}

# ============================================================
# AUTH TESTS
# ============================================================

def test_auth_register():
    """Test user registration"""
    global user_token
    print_test("Auth - Register New User")
    
    # Valid registration
    success, resp, data = make_request("POST", "/auth/register", data=TEST_USER)
    if not success:
        print_error("Registration failed")
        return False
    
    if "token" not in data or "user" not in data:
        print_error("Missing token or user in response")
        return False
    
    if data["user"]["credits"] != 3:
        print_error(f"Expected 3 credits, got {data['user']['credits']}")
        return False
    
    user_token = data["token"]
    print_success(f"User registered successfully with 3 credits")
    print_success(f"Token: {user_token[:20]}...")
    
    # Test duplicate email (409)
    success, resp, data = make_request("POST", "/auth/register", data=TEST_USER, expected_status=409)
    if not success:
        print_error("Duplicate email test failed")
        return False
    print_success("Duplicate email correctly rejected (409)")
    
    # Test invalid email (400)
    invalid_user = TEST_USER.copy()
    invalid_user["email"] = "invalid-email"
    success, resp, data = make_request("POST", "/auth/register", data=invalid_user, expected_status=400)
    if not success:
        print_error("Invalid email test failed")
        return False
    print_success("Invalid email correctly rejected (400)")
    
    # Test short password (400)
    short_pass_user = {
        "name": "Test",
        "email": "test2@example.com",
        "password": "123"
    }
    success, resp, data = make_request("POST", "/auth/register", data=short_pass_user, expected_status=400)
    if not success:
        print_error("Short password test failed")
        return False
    print_success("Short password correctly rejected (400)")
    
    return True

def test_auth_login():
    """Test user login"""
    print_test("Auth - Login")
    
    # Valid login
    success, resp, data = make_request("POST", "/auth/login", data={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    if not success:
        print_error("Login failed")
        return False
    
    if "token" not in data or "user" not in data:
        print_error("Missing token or user in response")
        return False
    
    print_success("User logged in successfully")
    
    # Test wrong password (401)
    success, resp, data = make_request("POST", "/auth/login", data={
        "email": TEST_USER["email"],
        "password": "WrongPassword123"
    }, expected_status=401)
    if not success:
        print_error("Wrong password test failed")
        return False
    print_success("Wrong password correctly rejected (401)")
    
    return True

def test_auth_me():
    """Test get current user"""
    print_test("Auth - Get Current User")
    
    # With valid token
    success, resp, data = make_request("GET", "/auth/me", token=user_token)
    if not success:
        print_error("Get user failed")
        return False
    
    if "user" not in data:
        print_error("Missing user in response")
        return False
    
    print_success(f"User retrieved: {data['user']['email']}")
    
    # Without token (401)
    success, resp, data = make_request("GET", "/auth/me", expected_status=401)
    if not success:
        print_error("Unauthorized test failed")
        return False
    print_success("Unauthorized request correctly rejected (401)")
    
    return True

def test_auth_forgot_reset_password():
    """Test forgot and reset password flow"""
    print_test("Auth - Forgot & Reset Password")
    
    # Forgot password
    success, resp, data = make_request("POST", "/auth/forgot-password", data={
        "email": TEST_USER["email"]
    })
    if not success:
        print_error("Forgot password failed")
        return False
    
    if "demoResetCode" not in data:
        print_error("Missing demoResetCode in response")
        return False
    
    reset_code = data["demoResetCode"]
    print_success(f"Reset code received: {reset_code}")
    
    # Reset password
    new_password = "NewSecurePass456"
    success, resp, data = make_request("POST", "/auth/reset-password", data={
        "email": TEST_USER["email"],
        "code": reset_code,
        "password": new_password
    })
    if not success:
        print_error("Reset password failed")
        return False
    
    print_success("Password reset successful")
    
    # Login with new password
    success, resp, data = make_request("POST", "/auth/login", data={
        "email": TEST_USER["email"],
        "password": new_password
    })
    if not success:
        print_error("Login with new password failed")
        return False
    
    print_success("Login with new password successful")
    
    # Update global token
    global user_token
    user_token = data["token"]
    
    return True

def test_admin_login():
    """Test admin login"""
    global admin_token
    print_test("Auth - Admin Login")
    
    success, resp, data = make_request("POST", "/auth/login", data=ADMIN_CREDS)
    if not success:
        print_error("Admin login failed")
        return False
    
    if "token" not in data or "user" not in data:
        print_error("Missing token or user in response")
        return False
    
    if data["user"]["role"] != "admin":
        print_error(f"Expected admin role, got {data['user']['role']}")
        return False
    
    admin_token = data["token"]
    print_success(f"Admin logged in successfully")
    print_success(f"Admin token: {admin_token[:20]}...")
    
    return True

# ============================================================
# IMEI/SERIAL CHECK TESTS
# ============================================================

def test_imei_check():
    """Test IMEI check endpoint"""
    global search_id_imei
    print_test("IMEI Check")
    
    # Valid IMEI
    success, resp, data = make_request("POST", "/imei/check", token=user_token, data={
        "imei": TEST_IMEI
    })
    if not success:
        print_error("IMEI check failed")
        return False
    
    if "searchId" not in data or "free" not in data or "locked" not in data:
        print_error("Missing required fields in response")
        return False
    
    if not data["locked"]:
        print_error("Expected locked=true")
        return False
    
    if "Brand" not in data["free"] or "Model" not in data["free"]:
        print_error("Missing Brand or Model in free preview")
        return False
    
    search_id_imei = data["searchId"]
    model1 = data["free"]["Model"]
    print_success(f"IMEI check successful, searchId: {search_id_imei}")
    print_success(f"Free preview: {data['free']}")
    
    # Test same IMEI returns same model (deterministic)
    success, resp, data2 = make_request("POST", "/imei/check", token=user_token, data={
        "imei": TEST_IMEI
    })
    if not success:
        print_error("Second IMEI check failed")
        return False
    
    model2 = data2["free"]["Model"]
    if model1 != model2:
        print_error(f"IMEI check not deterministic: {model1} != {model2}")
        return False
    print_success("IMEI check is deterministic (same model returned)")
    
    # Test invalid IMEI (400)
    success, resp, data = make_request("POST", "/imei/check", token=user_token, data={
        "imei": "12345"
    }, expected_status=400)
    if not success:
        print_error("Invalid IMEI test failed")
        return False
    print_success("Invalid IMEI correctly rejected (400)")
    
    return True

def test_serial_check():
    """Test Serial check endpoint"""
    global search_id_serial
    print_test("Serial Check")
    
    # Valid serial
    success, resp, data = make_request("POST", "/serial/check", token=user_token, data={
        "serial": TEST_SERIAL
    })
    if not success:
        print_error("Serial check failed")
        return False
    
    if "searchId" not in data or "free" not in data or "locked" not in data:
        print_error("Missing required fields in response")
        return False
    
    if not data["locked"]:
        print_error("Expected locked=true")
        return False
    
    if "Brand" not in data["free"] or "Model" not in data["free"]:
        print_error("Missing Brand or Model in free preview")
        return False
    
    search_id_serial = data["searchId"]
    print_success(f"Serial check successful, searchId: {search_id_serial}")
    print_success(f"Free preview: {data['free']}")
    
    # Test invalid serial (400)
    success, resp, data = make_request("POST", "/serial/check", token=user_token, data={
        "serial": "123"
    }, expected_status=400)
    if not success:
        print_error("Invalid serial test failed")
        return False
    print_success("Invalid serial correctly rejected (400)")
    
    return True

# ============================================================
# UNLOCK / CREDITS TESTS
# ============================================================

def test_unlock_flow():
    """Test unlock premium report with credit deduction"""
    print_test("Unlock Premium Report - Credit Flow")
    
    # Get current credits
    success, resp, data = make_request("GET", "/auth/me", token=user_token)
    if not success:
        print_error("Failed to get user")
        return False
    
    initial_credits = data["user"]["credits"]
    print_success(f"Initial credits: {initial_credits}")
    
    # Unlock IMEI report (should deduct 1 credit)
    success, resp, data = make_request("POST", "/unlock", token=user_token, data={
        "searchId": search_id_imei
    })
    if not success:
        print_error("Unlock failed")
        return False
    
    if "premium" not in data or "credits" not in data:
        print_error("Missing premium or credits in response")
        return False
    
    if data["credits"] != initial_credits - 1:
        print_error(f"Expected {initial_credits - 1} credits, got {data['credits']}")
        return False
    
    print_success(f"Unlock successful, credits deducted: {initial_credits} -> {data['credits']}")
    print_success(f"Premium fields received: {list(data['premium'].keys())[:5]}...")
    
    # Unlock same searchId again (should NOT deduct another credit)
    success, resp, data2 = make_request("POST", "/unlock", token=user_token, data={
        "searchId": search_id_imei
    })
    if not success:
        print_error("Second unlock failed")
        return False
    
    if data2["credits"] != data["credits"]:
        print_error(f"Credits changed on second unlock: {data['credits']} -> {data2['credits']}")
        return False
    
    print_success("Second unlock did NOT deduct another credit (correct)")
    
    # Test unlock without auth (401)
    success, resp, data = make_request("POST", "/unlock", data={
        "searchId": search_id_imei
    }, expected_status=401)
    if not success:
        print_error("Unauthorized unlock test failed")
        return False
    print_success("Unauthorized unlock correctly rejected (401)")
    
    return True

def test_no_credits_unlock():
    """Test unlock when user has no credits"""
    print_test("Unlock - No Credits (402)")
    
    # Drain all credits by unlocking multiple times
    # First, get current credits
    success, resp, data = make_request("GET", "/auth/me", token=user_token)
    if not success:
        print_error("Failed to get user")
        return False
    
    current_credits = data["user"]["credits"]
    print_success(f"Current credits: {current_credits}")
    
    # Create new searches and unlock them to drain credits
    for i in range(current_credits):
        # Create a new search with different IMEI
        test_imei = f"35987654321{str(i).zfill(4)}"
        success, resp, search_data = make_request("POST", "/imei/check", token=user_token, data={
            "imei": test_imei
        })
        if not success:
            print_error(f"Failed to create search {i+1}")
            return False
        
        # Unlock it
        success, resp, unlock_data = make_request("POST", "/unlock", token=user_token, data={
            "searchId": search_data["searchId"]
        })
        if not success:
            print_error(f"Failed to unlock search {i+1}")
            return False
        
        print_success(f"Drained credit {i+1}/{current_credits}, remaining: {unlock_data['credits']}")
    
    # Now try to unlock with 0 credits (should get 402)
    test_imei_final = "359876543219999"
    success, resp, search_data = make_request("POST", "/imei/check", token=user_token, data={
        "imei": test_imei_final
    })
    if not success:
        print_error("Failed to create final search")
        return False
    
    success, resp, data = make_request("POST", "/unlock", token=user_token, data={
        "searchId": search_data["searchId"]
    }, expected_status=402)
    if not success:
        print_error("No credits test failed")
        return False
    
    if "code" not in data or data["code"] != "NO_CREDITS":
        print_error(f"Expected code NO_CREDITS, got {data.get('code')}")
        return False
    
    print_success("No credits correctly rejected with 402 and code NO_CREDITS")
    
    return True

# ============================================================
# PLANS / CHECKOUT TESTS
# ============================================================

def test_plans():
    """Test get plans endpoint"""
    print_test("Plans - Get All Plans")
    
    success, resp, data = make_request("GET", "/plans")
    if not success:
        print_error("Get plans failed")
        return False
    
    if "plans" not in data:
        print_error("Missing plans in response")
        return False
    
    if len(data["plans"]) != 4:
        print_error(f"Expected 4 plans, got {len(data['plans'])}")
        return False
    
    plan_ids = [p["id"] for p in data["plans"]]
    expected_ids = ["single", "starter", "technician", "business"]
    if not all(pid in plan_ids for pid in expected_ids):
        print_error(f"Missing expected plan IDs. Got: {plan_ids}")
        return False
    
    print_success(f"4 plans retrieved: {plan_ids}")
    
    return True

def test_checkout():
    """Test mock checkout to add credits"""
    print_test("Checkout - Mock Payment")
    
    # Get current credits
    success, resp, data = make_request("GET", "/auth/me", token=user_token)
    if not success:
        print_error("Failed to get user")
        return False
    
    initial_credits = data["user"]["credits"]
    print_success(f"Initial credits: {initial_credits}")
    
    # Buy starter plan (10 credits)
    success, resp, data = make_request("POST", "/checkout", token=user_token, data={
        "planId": "starter"
    })
    if not success:
        print_error("Checkout failed")
        return False
    
    if "order" not in data or "credits" not in data:
        print_error("Missing order or credits in response")
        return False
    
    if data["credits"] != initial_credits + 10:
        print_error(f"Expected {initial_credits + 10} credits, got {data['credits']}")
        return False
    
    if data["order"]["status"] != "paid":
        print_error(f"Expected order status 'paid', got {data['order']['status']}")
        return False
    
    print_success(f"Checkout successful, credits added: {initial_credits} -> {data['credits']}")
    print_success(f"Order created: {data['order']['id']}")
    
    return True

# ============================================================
# USER DATA TESTS
# ============================================================

def test_dashboard():
    """Test dashboard endpoint"""
    print_test("Dashboard - User Stats")
    
    success, resp, data = make_request("GET", "/dashboard", token=user_token)
    if not success:
        print_error("Dashboard failed")
        return False
    
    if "stats" not in data or "recent" not in data:
        print_error("Missing stats or recent in response")
        return False
    
    required_stats = ["credits", "searches", "reports", "orders"]
    if not all(key in data["stats"] for key in required_stats):
        print_error(f"Missing required stats. Got: {list(data['stats'].keys())}")
        return False
    
    print_success(f"Dashboard retrieved: {data['stats']}")
    
    # Test without auth (401)
    success, resp, data = make_request("GET", "/dashboard", expected_status=401)
    if not success:
        print_error("Unauthorized dashboard test failed")
        return False
    print_success("Unauthorized dashboard correctly rejected (401)")
    
    return True

def test_history():
    """Test search history endpoint"""
    print_test("History - Search History")
    
    success, resp, data = make_request("GET", "/history", token=user_token)
    if not success:
        print_error("History failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"History retrieved: {len(data['items'])} items")
    
    # Test without auth (401)
    success, resp, data = make_request("GET", "/history", expected_status=401)
    if not success:
        print_error("Unauthorized history test failed")
        return False
    print_success("Unauthorized history correctly rejected (401)")
    
    return True

def test_reports():
    """Test reports endpoint"""
    print_test("Reports - Premium Reports")
    
    success, resp, data = make_request("GET", "/reports", token=user_token)
    if not success:
        print_error("Reports failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Reports retrieved: {len(data['items'])} items")
    
    # Test without auth (401)
    success, resp, data = make_request("GET", "/reports", expected_status=401)
    if not success:
        print_error("Unauthorized reports test failed")
        return False
    print_success("Unauthorized reports correctly rejected (401)")
    
    return True

def test_orders():
    """Test orders endpoint"""
    print_test("Orders - Purchase History")
    
    success, resp, data = make_request("GET", "/orders", token=user_token)
    if not success:
        print_error("Orders failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Orders retrieved: {len(data['items'])} items")
    
    # Test without auth (401)
    success, resp, data = make_request("GET", "/orders", expected_status=401)
    if not success:
        print_error("Unauthorized orders test failed")
        return False
    print_success("Unauthorized orders correctly rejected (401)")
    
    return True

# ============================================================
# ADMIN TESTS
# ============================================================

def test_admin_stats():
    """Test admin stats endpoint"""
    print_test("Admin - Stats")
    
    success, resp, data = make_request("GET", "/admin/stats", token=admin_token)
    if not success:
        print_error("Admin stats failed")
        return False
    
    if "stats" not in data:
        print_error("Missing stats in response")
        return False
    
    required_stats = ["users", "searches", "reports", "orders", "contacts", "revenue"]
    if not all(key in data["stats"] for key in required_stats):
        print_error(f"Missing required stats. Got: {list(data['stats'].keys())}")
        return False
    
    print_success(f"Admin stats retrieved: {data['stats']}")
    
    # Test with non-admin user (403)
    success, resp, data = make_request("GET", "/admin/stats", token=user_token, expected_status=403)
    if not success:
        print_error("Non-admin access test failed")
        return False
    print_success("Non-admin user correctly rejected (403)")
    
    return True

def test_admin_users():
    """Test admin users endpoint"""
    print_test("Admin - Users List")
    
    success, resp, data = make_request("GET", "/admin/users", token=admin_token)
    if not success:
        print_error("Admin users failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Admin users retrieved: {len(data['items'])} users")
    
    return True

def test_admin_update_user():
    """Test admin update user credits"""
    print_test("Admin - Update User Credits")
    
    # Get a user ID (use the test user)
    success, resp, data = make_request("GET", "/auth/me", token=user_token)
    if not success:
        print_error("Failed to get user")
        return False
    
    user_id = data["user"]["id"]
    
    # Update credits to 100
    success, resp, data = make_request("PUT", f"/admin/users/{user_id}", token=admin_token, data={
        "credits": 100
    })
    if not success:
        print_error("Admin update user failed")
        return False
    
    if "user" not in data or data["user"]["credits"] != 100:
        print_error(f"Expected 100 credits, got {data.get('user', {}).get('credits')}")
        return False
    
    print_success(f"User credits updated to 100")
    
    return True

def test_admin_searches():
    """Test admin searches endpoint"""
    print_test("Admin - All Searches")
    
    success, resp, data = make_request("GET", "/admin/searches", token=admin_token)
    if not success:
        print_error("Admin searches failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Admin searches retrieved: {len(data['items'])} searches")
    
    return True

def test_admin_reports():
    """Test admin reports endpoint"""
    print_test("Admin - All Reports")
    
    success, resp, data = make_request("GET", "/admin/reports", token=admin_token)
    if not success:
        print_error("Admin reports failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Admin reports retrieved: {len(data['items'])} reports")
    
    return True

def test_admin_orders():
    """Test admin orders endpoint"""
    print_test("Admin - All Orders")
    
    success, resp, data = make_request("GET", "/admin/orders", token=admin_token)
    if not success:
        print_error("Admin orders failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Admin orders retrieved: {len(data['items'])} orders")
    
    return True

def test_admin_contacts():
    """Test admin contacts endpoint"""
    print_test("Admin - All Contacts")
    
    success, resp, data = make_request("GET", "/admin/contacts", token=admin_token)
    if not success:
        print_error("Admin contacts failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Admin contacts retrieved: {len(data['items'])} contacts")
    
    return True

def test_admin_plans():
    """Test admin plans endpoint"""
    print_test("Admin - All Plans")
    
    success, resp, data = make_request("GET", "/admin/plans", token=admin_token)
    if not success:
        print_error("Admin plans failed")
        return False
    
    if "items" not in data:
        print_error("Missing items in response")
        return False
    
    print_success(f"Admin plans retrieved: {len(data['items'])} plans")
    
    return True

def test_admin_update_plan():
    """Test admin update plan"""
    print_test("Admin - Update Plan Price")
    
    # Update starter plan price to 9.99
    success, resp, data = make_request("PUT", "/admin/plans/starter", token=admin_token, data={
        "price": 9.99
    })
    if not success:
        print_error("Admin update plan failed")
        return False
    
    if "plan" not in data or data["plan"]["price"] != 9.99:
        print_error(f"Expected price 9.99, got {data.get('plan', {}).get('price')}")
        return False
    
    print_success(f"Plan price updated to 9.99")
    
    # Restore original price
    success, resp, data = make_request("PUT", "/admin/plans/starter", token=admin_token, data={
        "price": 14.99
    })
    if not success:
        print_error("Failed to restore plan price")
        return False
    
    print_success("Plan price restored to 14.99")
    
    return True

# ============================================================
# CONTACT TESTS
# ============================================================

def test_contact():
    """Test contact form endpoint"""
    print_test("Contact - Submit Form")
    
    success, resp, data = make_request("POST", "/contact", data={
        "name": "Test User",
        "email": "test@example.com",
        "message": "This is a test message"
    })
    if not success:
        print_error("Contact form failed")
        return False
    
    if "message" not in data:
        print_error("Missing message in response")
        return False
    
    print_success("Contact form submitted successfully")
    
    # Test missing fields (400)
    success, resp, data = make_request("POST", "/contact", data={
        "name": "Test User"
    }, expected_status=400)
    if not success:
        print_error("Missing fields test failed")
        return False
    print_success("Missing fields correctly rejected (400)")
    
    return True

# ============================================================
# MAIN TEST RUNNER
# ============================================================

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("UnlockTap Backend API Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    tests = [
        # Auth tests
        ("Auth - Register", test_auth_register),
        ("Auth - Login", test_auth_login),
        ("Auth - Me", test_auth_me),
        ("Auth - Forgot/Reset Password", test_auth_forgot_reset_password),
        ("Auth - Admin Login", test_admin_login),
        
        # IMEI/Serial tests
        ("IMEI Check", test_imei_check),
        ("Serial Check", test_serial_check),
        
        # Unlock tests
        ("Unlock - Credit Flow", test_unlock_flow),
        ("Unlock - No Credits", test_no_credits_unlock),
        
        # Plans/Checkout tests
        ("Plans", test_plans),
        ("Checkout", test_checkout),
        
        # User data tests
        ("Dashboard", test_dashboard),
        ("History", test_history),
        ("Reports", test_reports),
        ("Orders", test_orders),
        
        # Admin tests
        ("Admin - Stats", test_admin_stats),
        ("Admin - Users", test_admin_users),
        ("Admin - Update User", test_admin_update_user),
        ("Admin - Searches", test_admin_searches),
        ("Admin - Reports", test_admin_reports),
        ("Admin - Orders", test_admin_orders),
        ("Admin - Contacts", test_admin_contacts),
        ("Admin - Plans", test_admin_plans),
        ("Admin - Update Plan", test_admin_update_plan),
        
        # Contact test
        ("Contact", test_contact),
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                failed_tests.append(name)
        except Exception as e:
            print_error(f"Test '{name}' crashed: {str(e)}")
            failed += 1
            failed_tests.append(name)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed_tests:
        print("\nFailed tests:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
    
    print("="*60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

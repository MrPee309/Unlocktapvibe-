#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Build UnlockTap - Apple IMEI & Serial checker with auth, credits, dashboard, admin, mock verification data and mock payments (Next.js + MongoDB, no external keys)."

backend:
  - task: "Auth (register, login, forgot/reset password, me)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Local credentials auth using Node crypto pbkdf2 hashing + HMAC signed token. Register gives 3 free credits. Forgot returns demoResetCode. Admin seeded admin@unlocktap.com/Admin@123."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL AUTH TESTS PASSED: Register returns token + user with 3 credits. Duplicate email (409), invalid email (400), short password (400) all correctly rejected. Login works with correct credentials, wrong password returns 401. GET /auth/me returns user with Bearer token, 401 without token. Forgot password returns demoResetCode, reset password works, login with new password successful. Admin login (admin@unlocktap.com/Admin@123) returns user with role='admin'."
        -working: true
        -agent: "testing"
        -comment: "✅ FOCUSED AUTH-ONLY VERIFICATION COMPLETE (22/22 tests passed): All registration scenarios validated (valid returns token+user with 3 credits+role=user+no password field, duplicate 409, invalid email 400, short password 400, missing fields 400). All login scenarios validated (valid credentials 200, wrong password 401, non-existent email 401, missing fields 400). Admin login verified (admin@unlocktap.com/Admin@123 returns role='admin'). GET /auth/me validated (valid Bearer token 200, no token 401, malformed token 401, tampered token 401 with HMAC signature verification working). Forgot password validated (existing email returns demoResetCode, non-existent email returns 200 with null code). Reset password full flow validated (reset successful, login with new password works, login with old password correctly rejected 401, wrong code returns 400). Token structure verified (contains sub, role, exp). Session persistence confirmed (multiple /auth/me calls work consistently with same token). All security measures working correctly."
  - task: "IMEI check + free preview"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /imei/check validates 15 digits, returns free preview + searchId, saves searchhistory. Deterministic mock via seeded RNG."
        -working: true
        -agent: "testing"
        -comment: "✅ IMEI CHECK PASSED: POST /api/imei/check with valid 15-digit IMEI returns searchId, free preview (Brand, Model, Model Number, Capacity, Color), and locked:true. Invalid IMEI (non-15-digit) correctly returns 400. Deterministic check verified - same IMEI returns same model consistently."
  - task: "Serial check + free preview"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /serial/check validates 8-14 alphanumeric, returns free preview + searchId."
        -working: true
        -agent: "testing"
        -comment: "✅ SERIAL CHECK PASSED: POST /api/serial/check with valid 8-14 alphanumeric serial returns searchId, free preview (Brand, Model, Group, Type), and locked:true. Invalid serial (less than 8 chars) correctly returns 400."
  - task: "Unlock premium report (spends 1 credit)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /unlock requires auth, deducts 1 credit once, creates report record, returns premium fields. 402 NO_CREDITS when insufficient."
        -working: true
        -agent: "testing"
        -comment: "✅ UNLOCK & CREDITS FLOW PASSED: POST /api/unlock with valid searchId and auth deducts 1 credit and returns premium fields. Second unlock of SAME searchId does NOT deduct another credit (correct behavior). Unlocking without auth returns 401. When user has 0 credits, unlock returns 402 with code='NO_CREDITS'. All credit logic working correctly."
  - task: "Plans + mock checkout"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET /plans seeded (single/starter/technician/business). POST /checkout mock payment adds credits + creates order."
        -working: true
        -agent: "testing"
        -comment: "✅ PLANS & CHECKOUT PASSED: GET /api/plans returns 4 plans (single, starter, technician, business) with correct structure. POST /api/checkout with planId='starter' successfully adds 10 credits, creates order with status='paid', and returns updated credits + order details. Mock payment flow working correctly."
  - task: "Dashboard, history, reports, orders"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Auth-protected user data endpoints."
        -working: true
        -agent: "testing"
        -comment: "✅ USER DATA ENDPOINTS PASSED: GET /api/dashboard returns stats (credits, searches, reports, orders) and recent searches. GET /api/history returns user's search history. GET /api/reports returns user's premium reports. GET /api/orders returns user's purchase history. All endpoints correctly return 401 when accessed without authentication."
  - task: "Admin endpoints (stats, users, plans, searches, orders, contacts)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Role-guarded admin endpoints. PUT users adjusts credits/role/banned. PUT plans edits pricing."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL ADMIN ENDPOINTS PASSED: GET /api/admin/stats returns aggregate stats (users, searches, reports, orders, contacts, revenue). GET /api/admin/users returns all users. PUT /api/admin/users/{id} successfully updates user credits. GET /api/admin/searches, /api/admin/reports, /api/admin/orders, /api/admin/contacts all return correct data. GET /api/admin/plans returns all plans. PUT /api/admin/plans/{id} successfully updates plan price. Non-admin users correctly receive 403 when accessing admin routes."
  - task: "Contact form"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /contact saves to contacts collection."
        -working: true
        -agent: "testing"
        -comment: "✅ CONTACT FORM PASSED: POST /api/contact with name, email, and message successfully saves to contacts collection and returns success message. Missing fields correctly return 400 error."

frontend:
  - task: "Full SPA UI (home, checkers, auth, dashboard, admin, i18n)"
    implemented: true
    working: "NA"
    file: "app/page.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Built but not yet tested by frontend agent (awaiting user permission)."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "Auth (register, login, forgot/reset password, me)"
    - "IMEI check + free preview"
    - "Serial check + free preview"
    - "Unlock premium report (spends 1 credit)"
    - "Plans + mock checkout"
    - "Admin endpoints (stats, users, plans, searches, orders, contacts)"
  stuck_tasks: []
  test_all: true
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Backend implemented in single catch-all route. Please test all endpoints. Admin login: admin@unlocktap.com / Admin@123. Test full flow: register -> imei/check -> unlock (should require credits) -> checkout to add credits -> unlock success. Use Bearer token from login/register in Authorization header."
    -agent: "testing"
    -message: "✅ BACKEND TESTING COMPLETE - ALL 25 TESTS PASSED! Comprehensive testing performed on all backend endpoints. Auth flow (register/login/forgot-reset/me/admin) working perfectly. IMEI/Serial checks return correct data and are deterministic. Credit system working correctly (deducts once per searchId, returns 402 NO_CREDITS when insufficient). Plans and checkout add credits successfully. All user data endpoints (dashboard/history/reports/orders) working with proper auth. All admin endpoints working with role-based access control (403 for non-admins). Contact form working. No critical issues found. Backend is production-ready."
    -agent: "testing"
    -message: "✅ FOCUSED AUTH-ONLY VERIFICATION COMPLETE - 22/22 TESTS PASSED (100% success rate). Performed comprehensive auth testing per review request: (1) POST /api/auth/register validated all scenarios - valid registration returns token+user with 3 credits+role=user+no password field in response, duplicate email correctly returns 409, invalid email format returns 400, password<6 chars returns 400, missing fields returns 400. (2) POST /api/auth/login validated all scenarios - valid credentials return 200 with token+user, wrong password returns 401, non-existent email returns 401, missing fields return 400. (3) Admin login verified - admin@unlocktap.com/Admin@123 successfully returns 200 with user.role='admin'. (4) GET /api/auth/me validated all scenarios - valid Bearer token returns 200 with user, no token returns 401, malformed token returns 401, tampered token returns 401 (HMAC signature verification working correctly). (5) POST /api/auth/forgot-password validated - existing email returns 200 with demoResetCode, non-existent email returns 200 with null code (no error). (6) POST /api/auth/reset-password full flow validated - registered new user, requested forgot-password to get demoResetCode, reset password successful (200), login with NEW password successful (200), login with OLD password correctly rejected (401), wrong/invalid reset code returns 400. (7) Token structure verified - payload contains sub (user id), role, and exp (expiry timestamp). Session persistence confirmed - multiple /api/auth/me calls work consistently with same token. All security measures (HMAC signature verification, password hashing, token expiry) working correctly. NO CODE MODIFICATIONS MADE. Auth system is secure and production-ready."

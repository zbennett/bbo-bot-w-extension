#!/usr/bin/env python3
"""
Test script to verify dashboard refactoring works
"""

import sys
import time

# Test 1: Import original dashboard
print("Test 1: Importing original web_dashboard module...")
try:
    import web_dashboard as DashboardBroadcaster
    print("✅ Original web_dashboard imports successfully")
except Exception as e:
    print(f"❌ Failed to import web_dashboard: {e}")
    sys.exit(1)

# Test 2: Check that all public API methods exist
print("\nTest 2: Checking public API methods...")
required_methods = [
    'update_new_deal',
    'update_card_played',
    'update_bid',
    'update_contract',
    'update_recommendation',
    'update_dd_analysis',
    'update_active_player',
    'set_bottom_seat'
]

for method in required_methods:
    if hasattr(DashboardBroadcaster.DashboardBroadcaster, method):
        print(f"  ✅ {method} exists")
    else:
        print(f"  ❌ {method} missing")
        sys.exit(1)

# Test 3: Try importing new modular backend
print("\nTest 3: Importing new modular backend...")
try:
    from web import dashboard
    print("✅ New web.dashboard module imports successfully")
except Exception as e:
    print(f"❌ Failed to import web.dashboard: {e}")
    sys.exit(1)

# Test 4: Check Flask app exists
print("\nTest 4: Checking Flask app...")
try:
    import web_dashboard
    app = web_dashboard.app
    print(f"✅ Flask app exists: {app}")
    
    # Check routes
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"  Routes: {routes}")
    
    if '/' in routes and '/modular' in routes and '/classic' in routes:
        print("  ✅ All expected routes present")
    else:
        print("  ❌ Missing expected routes")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Flask app check failed: {e}")
    sys.exit(1)

# Test 5: Start server briefly to verify it works
print("\nTest 5: Starting dashboard server briefly...")
try:
    import threading
    
    def run_server():
        DashboardBroadcaster.socketio.run(
            DashboardBroadcaster.app,
            host='127.0.0.1',
            port=5555,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give it time to start
    time.sleep(2)
    
    if server_thread.is_alive():
        print("✅ Dashboard server started successfully")
    else:
        print("❌ Dashboard server failed to start")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Server test failed: {e}")
    sys.exit(1)

# Test 6: Test calling API methods (without Socket.IO clients)
print("\nTest 6: Testing API methods...")
try:
    DashboardBroadcaster.DashboardBroadcaster.set_bottom_seat('W')
    print("  ✅ set_bottom_seat() works")
    
    DashboardBroadcaster.DashboardBroadcaster.update_new_deal(
        board_number=1,
        dealer='N',
        vulnerability='None',
        hands={'N': ['SA', 'SK'], 'E': [], 'S': [], 'W': []}
    )
    print("  ✅ update_new_deal() works")
    
    DashboardBroadcaster.DashboardBroadcaster.update_contract('3NT', 'N')
    print("  ✅ update_contract() works")
    
    DashboardBroadcaster.DashboardBroadcaster.update_active_player('N')
    print("  ✅ update_active_player() works")
    
except Exception as e:
    print(f"  ❌ API method test failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ ALL TESTS PASSED!")
print("="*50)
print("\nDashboard refactoring is backward compatible and working correctly.")
print("You can access:")
print("  - Original dashboard: http://localhost:5001/")
print("  - Modular dashboard: http://localhost:5001/modular")
print("  - Classic dashboard: http://localhost:5001/classic")

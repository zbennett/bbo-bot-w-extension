#!/usr/bin/env python3
"""
Test that rubber scoring updates properly through the dashboard broadcaster
"""
import time
from web_dashboard import start_dashboard, DashboardBroadcaster
from rubber_scoring import RubberScoring

print("🚀 Starting test of rubber scoring integration\n")

# Start dashboard
print("1. Starting dashboard...")
start_dashboard(port=5001)
time.sleep(2)

# Initialize rubber scorer
print("2. Initializing rubber scorer...")
rubber_scorer = RubberScoring()

# Send initial state
print("3. Broadcasting initial rubber score...")
initial_status = rubber_scorer.get_rubber_status()
print(f"   Initial status: rubber_number={initial_status['rubber_number']}, hand_count={initial_status['hand_count']}")
DashboardBroadcaster.update_rubber_score(initial_status)
time.sleep(1)

# Simulate a hand being played
print("\n4. Simulating hand: 3NT by N, made 9 tricks...")
result = rubber_scorer.record_hand_result('3NT', 'N', 9)
print(f"   Result: {result['score']['partnership']} +{result['score']['total']}")
print(f"   Rubber status: NS {result['rubber_status']['ns']['total']} - EW {result['rubber_status']['ew']['total']}")

# Broadcast update
print("5. Broadcasting rubber score update...")
DashboardBroadcaster.update_rubber_score(result['rubber_status'])
time.sleep(1)

# Simulate another hand
print("\n6. Simulating hand: 4S by E, made 10 tricks...")
result2 = rubber_scorer.record_hand_result('4S', 'E', 10)
print(f"   Result: {result2['score']['partnership']} +{result2['score']['total']}")
print(f"   Rubber status: NS {result2['rubber_status']['ns']['total']} - EW {result2['rubber_status']['ew']['total']}")

# Broadcast update
print("7. Broadcasting rubber score update...")
DashboardBroadcaster.update_rubber_score(result2['rubber_status'])

print("\n✅ Test complete!")
print(f"📊 Open http://localhost:5001 to view the dashboard")
print(f"   You should see:")
print(f"   - Rubber #1 with 2 hands played")
print(f"   - NS: {result2['rubber_status']['ns']['total']} pts (1 game, vulnerable)")
print(f"   - EW: {result2['rubber_status']['ew']['total']} pts (1 game, vulnerable)")
print(f"   - Last hand: 4S by E → 10 tricks")
print("\nPress Ctrl+C to exit...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n👋 Exiting test")

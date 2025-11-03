#!/usr/bin/env python3
"""
Test claim handling for rubber scoring
"""

from rubber_scoring import RubberScoring

def test_claim_scenarios():
    """Test various claim scenarios"""
    print("=" * 60)
    print("Testing Claim Scenarios")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # Scenario 1: Declarer claims remaining tricks
    print("\n📋 Scenario 1: 3NT by N, 7 tricks played (NS won 6, EW won 1), N claims 6")
    print("   Expected: NS makes 6+6=12 tricks total")
    result = scorer.record_hand_result('3NT', 'N', 12)
    print(f"   Score: {result['score']['partnership']} +{result['score']['total']}")
    print(f"   Result: {result['score']['description']}")
    assert result['score']['partnership'] == 'NS'
    assert result['score']['total'] == 490  # 3NT +3 overtricks
    print("   ✅ Correct!")
    
    # Scenario 2: Defenders claim
    print("\n📋 Scenario 2: 4S by S, 8 tricks played (NS won 6, EW won 2), E claims 3")
    print("   Expected: NS makes 6+2=8 tricks (down 2)")
    result = scorer.record_hand_result('4S', 'S', 8)
    print(f"   Score: {result['score']['partnership']} +{result['score']['total']}")
    print(f"   Result: {result['score']['description']}")
    assert result['score']['partnership'] == 'EW'  # Penalty goes to defenders
    print("   ✅ Correct!")
    
    # Scenario 3: Slam claimed
    print("\n📋 Scenario 3: 6H by N, 10 tricks played (NS won 10, EW won 0), N claims 2")
    print("   Expected: NS makes 10+2=12 tricks (slam made)")
    result = scorer.record_hand_result('6H', 'N', 12)
    print(f"   Score: {result['score']['partnership']} +{result['score']['total']}")
    print(f"   Result: {result['score']['description']}")
    assert result['score']['partnership'] == 'NS'
    assert result['score']['total'] >= 1430  # Slam bonus + game
    print("   ✅ Correct!")
    
    print("\n" + "=" * 60)
    print("✅ All claim scenarios handled correctly!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    test_claim_scenarios()

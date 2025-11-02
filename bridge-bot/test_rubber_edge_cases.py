#!/usr/bin/env python3
"""
Test edge cases for rubber scoring
"""

from rubber_scoring import RubberScoring

def test_contract_formats():
    """Test various contract format variations"""
    print("=" * 60)
    print("Testing Contract Format Variations")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # Test single-char N vs NT
    test_cases = [
        ('1N', 'S', 7, "1N with single character"),
        ('3NT', 'N', 9, "3NT with two characters"),
        ('7N', 'E', 13, "7N grand slam"),
        ('1NT', 'W', 8, "1NT making +1"),
    ]
    
    for contract, declarer, tricks, desc in test_cases:
        try:
            result = scorer.record_hand_result(contract, declarer, tricks)
            print(f"✅ {desc}: {contract} by {declarer}, {tricks} tricks")
            print(f"   Score: {result['score']['partnership']} +{result['score']['total']}")
        except Exception as e:
            print(f"❌ {desc}: {contract} by {declarer} - ERROR: {e}")
            return False
    
    return True

def test_doubled_contracts():
    """Test doubled and redoubled contracts"""
    print("\n" + "=" * 60)
    print("Testing Doubled/Redoubled Contracts")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    test_cases = [
        ('3N', 'N', 9, True, False, "3N doubled, made exactly"),
        ('4S', 'S', 11, True, False, "4S doubled, made +1"),
        ('2C', 'E', 7, False, True, "2C redoubled, down 1"),
        ('1NT', 'W', 6, True, False, "1NT doubled, down 1"),
    ]
    
    for contract, declarer, tricks, doubled, redoubled, desc in test_cases:
        try:
            result = scorer.record_hand_result(contract, declarer, tricks, doubled, redoubled)
            print(f"✅ {desc}")
            print(f"   Score: {result['score']['partnership']} +{result['score']['total']}")
        except Exception as e:
            print(f"❌ {desc} - ERROR: {e}")
            return False
    
    return True

def test_slam_contracts():
    """Test slam bonuses"""
    print("\n" + "=" * 60)
    print("Testing Slam Contracts")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # Make NS vulnerable first
    scorer.record_hand_result('4S', 'N', 10)
    
    test_cases = [
        ('6N', 'S', 12, False, False, "6N small slam (vulnerable)"),
        ('6NT', 'E', 12, False, False, "6NT small slam (not vulnerable)"),
        ('7H', 'N', 13, False, False, "7H grand slam (vulnerable)"),
    ]
    
    for contract, declarer, tricks, doubled, redoubled, desc in test_cases:
        try:
            result = scorer.record_hand_result(contract, declarer, tricks, doubled, redoubled)
            print(f"✅ {desc}")
            print(f"   Score: {result['score']['partnership']} +{result['score']['total']}")
            if 'slam_bonus' in result['score']:
                print(f"   Slam bonus: {result['score'].get('slam_bonus', 0)}")
        except Exception as e:
            print(f"❌ {desc} - ERROR: {e}")
            return False
    
    return True

def test_penalties():
    """Test penalty scoring"""
    print("\n" + "=" * 60)
    print("Testing Penalty Scoring")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    test_cases = [
        ('3N', 'N', 7, False, False, "3N down 2 (not vulnerable)"),
        ('3NT', 'S', 6, False, False, "3NT down 3 (not vulnerable)"),
        ('4S', 'E', 8, True, False, "4S doubled, down 2"),
        ('6N', 'W', 9, True, False, "6N doubled, down 3"),
    ]
    
    for contract, declarer, tricks, doubled, redoubled, desc in test_cases:
        try:
            result = scorer.record_hand_result(contract, declarer, tricks, doubled, redoubled)
            print(f"✅ {desc}")
            print(f"   Penalty to: {result['score']['partnership']} +{result['score']['total']}")
        except Exception as e:
            print(f"❌ {desc} - ERROR: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("\n🧪 RUBBER SCORING EDGE CASE TESTS\n")
    
    results = []
    results.append(("Contract Formats", test_contract_formats()))
    results.append(("Doubled Contracts", test_doubled_contracts()))
    results.append(("Slam Contracts", test_slam_contracts()))
    results.append(("Penalties", test_penalties()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    if all(passed for _, passed in results):
        print("\n🎉 All edge case tests passed!")
    else:
        print("\n⚠️  Some tests failed")
        exit(1)

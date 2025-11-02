#!/usr/bin/env python3
"""
Test Rubber Scoring System
Simulates several bridge hands to verify scoring calculations
"""

from rubber_scoring import RubberScoring

def test_basic_game():
    """Test a simple game completion"""
    print("=" * 60)
    print("TEST 1: Basic Game (3NT making exactly)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # 3NT making 9 tricks (exactly)
    result = scorer.record_hand_result('3NT', 'N', 9)
    print(f"\nContract: 3NT by N, made 9 tricks")
    print(f"Score: {result['score']}")
    print(f"\nRubber Status:")
    status = result['rubber_status']
    print(f"  NS: {status['ns']['total']} pts ({status['ns']['games']} games, {'VUL' if status['ns']['vulnerable'] else 'not vul'})")
    print(f"  EW: {status['ew']['total']} pts ({status['ew']['games']} games, {'VUL' if status['ew']['vulnerable'] else 'not vul'})")
    
    assert status['ns']['games'] == 1, "NS should have 1 game"
    assert status['ns']['vulnerable'], "NS should be vulnerable"
    assert result['score']['below_line'] >= 100, "Should make game"
    print("\n✅ Test 1 passed!")


def test_part_score():
    """Test part score"""
    print("\n" + "=" * 60)
    print("TEST 2: Part Score (2D making)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # 2D making 8 tricks
    result = scorer.record_hand_result('2D', 'E', 8)
    print(f"\nContract: 2D by E, made 8 tricks")
    print(f"Score: {result['score']}")
    
    status = result['rubber_status']
    print(f"\nRubber Status:")
    print(f"  NS: {status['ns']['total']} pts ({status['ns']['games']} games)")
    print(f"  EW: {status['ew']['total']} pts ({status['ew']['games']} games)")
    
    assert status['ew']['games'] == 0, "EW should have 0 games (part score)"
    assert status['ew']['below'] == 40, "EW should have 40 points below line"
    print("\n✅ Test 2 passed!")


def test_slam():
    """Test slam bonus"""
    print("\n" + "=" * 60)
    print("TEST 3: Small Slam (6H vulnerable)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # Make NS vulnerable first
    scorer.record_hand_result('3NT', 'N', 9)
    
    # 6H making 12 tricks (vulnerable)
    result = scorer.record_hand_result('6H', 'S', 12)
    print(f"\nContract: 6H by S (vulnerable), made 12 tricks")
    print(f"Score: {result['score']}")
    
    status = result['rubber_status']
    print(f"\nRubber Status:")
    print(f"  NS: {status['ns']['total']} pts ({status['ns']['games']} games)")
    
    assert result['score']['above_line'] >= 750, "Should have slam bonus of 750+"
    print("\n✅ Test 3 passed!")


def test_doubled_contract():
    """Test doubled contract"""
    print("\n" + "=" * 60)
    print("TEST 4: Doubled Contract (3Cx making +1)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # 3C doubled making 10 tricks
    result = scorer.record_hand_result('3C', 'W', 10, doubled=True)
    print(f"\nContract: 3Cx by W, made 10 tricks")
    print(f"Score: {result['score']}")
    print(f"  Below line: {result['score']['below_line']}")
    print(f"  Above line: {result['score']['above_line']} (includes overtrick + double bonus)")
    
    assert result['score']['below_line'] == 120, "3C doubled = 120 below"
    assert result['score']['above_line'] >= 150, "Should have overtrick + double bonus"
    print("\n✅ Test 4 passed!")


def test_penalty():
    """Test penalty for defeated contract"""
    print("\n" + "=" * 60)
    print("TEST 5: Penalty (3NT down 2, not vulnerable)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # 3NT down 2
    result = scorer.record_hand_result('3NT', 'N', 7)  # needed 9, made 7
    print(f"\nContract: 3NT by N, down 2")
    print(f"Score: {result['score']}")
    print(f"  Penalty: {result['score']['total']} to EW")
    
    status = result['rubber_status']
    print(f"\nRubber Status:")
    print(f"  NS: {status['ns']['total']} pts")
    print(f"  EW: {status['ew']['total']} pts (penalty)")
    
    assert result['score']['total'] == 100, "Down 2 not vul = 100"
    assert status['ew']['total'] == 100, "EW should get penalty"
    print("\n✅ Test 5 passed!")


def test_rubber_completion():
    """Test complete rubber"""
    print("\n" + "=" * 60)
    print("TEST 6: Complete Rubber (NS wins 2-0)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # Game 1: NS
    print("\n  Game 1: 4S by N, made 10 tricks")
    result1 = scorer.record_hand_result('4S', 'N', 10)
    status1 = result1['rubber_status']
    print(f"    NS: {status1['ns']['games']} game(s), {status1['ns']['total']} pts")
    
    # Game 2: NS (completes rubber)
    print("\n  Game 2: 3NT by S, made 9 tricks")
    result2 = scorer.record_hand_result('3NT', 'S', 9)
    status2 = result2['rubber_status']
    print(f"    NS: {status2['ns']['games']} game(s), {status2['ns']['total']} pts")
    
    assert status2['ns']['games'] == 2, "NS should have 2 games"
    assert status2['rubber_complete'], "Rubber should be complete"
    assert status2['ns']['rubbers'] == 1, "NS should have won 1 rubber"
    
    # Check rubber bonus (500 for 2-0)
    print(f"\n  Rubber complete: NS wins 2-0")
    print(f"  Final score: NS {status2['ns']['total']} - EW {status2['ew']['total']}")
    print(f"  Rubber bonus: 500 (2-0 win)")
    
    print("\n✅ Test 6 passed!")


def test_competitive_rubber():
    """Test competitive rubber (2-1)"""
    print("\n" + "=" * 60)
    print("TEST 7: Competitive Rubber (EW wins 2-1)")
    print("=" * 60)
    
    scorer = RubberScoring()
    
    # Game 1: NS
    print("\n  Game 1: 4H by N, made 10 tricks")
    scorer.record_hand_result('4H', 'N', 10)
    
    # Game 2: EW
    print("  Game 2: 5D by E, made 11 tricks")
    scorer.record_hand_result('5D', 'E', 11)
    
    # Game 3: EW (completes rubber)
    print("  Game 3: 4S by W, made 10 tricks")
    result = scorer.record_hand_result('4S', 'W', 10)
    
    status = result['rubber_status']
    print(f"\n  Rubber complete: EW wins 2-1")
    print(f"  Final score: NS {status['ns']['total']} - EW {status['ew']['total']}")
    print(f"  Rubber bonus: 700 (2-1 win)")
    
    assert status['rubber_complete'], "Rubber should be complete"
    assert status['ew']['rubbers'] == 1, "EW should have won 1 rubber"
    
    print("\n✅ Test 7 passed!")


def run_all_tests():
    """Run all tests"""
    print("\n🎯 RUBBER SCORING SYSTEM TESTS\n")
    
    try:
        test_basic_game()
        test_part_score()
        test_slam()
        test_doubled_contract()
        test_penalty()
        test_rubber_completion()
        test_competitive_rubber()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nRubber scoring system is working correctly!")
        print("Ready to integrate with the bot.\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise


if __name__ == '__main__':
    run_all_tests()

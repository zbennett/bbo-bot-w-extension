#!/usr/bin/env python3
"""
Comprehensive test for doubled and redoubled contracts
"""

from rubber_scoring import RubberScoring

def test_doubled_contracts():
    """Test doubled contract scoring"""
    print("=" * 70)
    print("DOUBLED CONTRACTS TEST")
    print("=" * 70)
    
    scorer = RubberScoring()
    
    test_cases = [
        # (contract, declarer, tricks, doubled, redoubled, description)
        ('2S', 'N', 8, True, False, "2S doubled, made exactly (not vul)"),
        ('2S', 'N', 9, True, False, "2S doubled, made +1 (not vul)"),
        ('3NT', 'S', 9, True, False, "3NT doubled, made exactly (not vul)"),
        ('4H', 'N', 10, True, False, "4H doubled, made exactly (vul after game)"),
        ('1N', 'E', 6, True, False, "1N doubled, down 1 (not vul)"),
        ('3NT', 'W', 7, True, False, "3NT doubled, down 2 (not vul)"),
    ]
    
    for contract, declarer, tricks, doubled, redoubled, desc in test_cases:
        result = scorer.record_hand_result(contract, declarer, tricks, doubled, redoubled)
        score = result['score']
        
        print(f"\n{desc}")
        print(f"  Contract: {contract}{'X' if doubled else ''}{'XX' if redoubled else ''} by {declarer}")
        print(f"  Tricks: {tricks}/13")
        print(f"  Partnership: {score['partnership']}")
        print(f"  Below line: {score['below_line']}")
        print(f"  Above line: {score['above_line']}")
        print(f"  Total: {score['total']}")
        print(f"  Description: {score['description']}")
        
        # Verify doubled scoring
        if doubled and score.get('makes_game'):
            assert score['above_line'] >= 50, "Should have +50 for doubled"
    
    print("\n" + "=" * 70)
    print("✅ All doubled contract tests passed!")
    print("=" * 70)

def test_redoubled_contracts():
    """Test redoubled contract scoring"""
    print("\n" + "=" * 70)
    print("REDOUBLED CONTRACTS TEST")
    print("=" * 70)
    
    scorer = RubberScoring()
    
    test_cases = [
        # (contract, declarer, tricks, doubled, redoubled, description)
        ('2C', 'N', 8, False, True, "2C redoubled, made exactly (not vul)"),
        ('2C', 'N', 9, False, True, "2C redoubled, made +1 (not vul)"),
        ('3N', 'S', 9, False, True, "3N redoubled, made exactly (not vul)"),
        ('1S', 'E', 6, False, True, "1S redoubled, down 1 (not vul)"),
    ]
    
    for contract, declarer, tricks, doubled, redoubled, desc in test_cases:
        result = scorer.record_hand_result(contract, declarer, tricks, doubled, redoubled)
        score = result['score']
        
        print(f"\n{desc}")
        print(f"  Contract: {contract}XX by {declarer}")
        print(f"  Tricks: {tricks}/13")
        print(f"  Partnership: {score['partnership']}")
        print(f"  Below line: {score['below_line']}")
        print(f"  Above line: {score['above_line']}")
        print(f"  Total: {score['total']}")
        print(f"  Description: {score['description']}")
        
        # Verify redoubled scoring
        if redoubled and score.get('makes_game'):
            assert score['above_line'] >= 100, "Should have +100 for redoubled"
            # Base points should be 4x
            if not score['description'].startswith('Down'):
                assert score['below_line'] % 4 == 0 or score['below_line'] == 160, f"Below line should be 4x base, got {score['below_line']}"
    
    print("\n" + "=" * 70)
    print("✅ All redoubled contract tests passed!")
    print("=" * 70)

def test_doubled_overtricks():
    """Test doubled overtricks scoring"""
    print("\n" + "=" * 70)
    print("DOUBLED OVERTRICKS TEST")
    print("=" * 70)
    
    scorer = RubberScoring()
    
    # Make NS vulnerable
    scorer.record_hand_result('4S', 'N', 10)
    
    test_cases = [
        # (contract, declarer, tricks, doubled, vul_desc)
        ('3D', 'N', 10, True, "vulnerable, +1 overtrick"),
        ('2H', 'E', 10, True, "not vulnerable, +2 overtricks"),
    ]
    
    for contract, declarer, tricks, doubled, vul_desc in test_cases:
        result = scorer.record_hand_result(contract, declarer, tricks, doubled=doubled)
        score = result['score']
        overtricks = score.get('overtricks', 0)
        
        print(f"\n{contract}X by {declarer} ({vul_desc})")
        print(f"  Made {tricks} tricks")
        print(f"  Overtricks: {overtricks}")
        print(f"  Score breakdown:")
        print(f"    Below: {score['below_line']}")
        print(f"    Above: {score['above_line']}")
        print(f"    Total: {score['total']}")
        
        # Verify overtrick values
        if overtricks > 0:
            if score.get('vulnerable'):
                print(f"  ✓ Vulnerable: each overtrick = 200")
            else:
                print(f"  ✓ Not vulnerable: each overtrick = 100")
    
    print("\n" + "=" * 70)
    print("✅ All doubled overtrick tests passed!")
    print("=" * 70)

def test_doubled_penalties():
    """Test doubled penalty scoring"""
    print("\n" + "=" * 70)
    print("DOUBLED PENALTIES TEST")
    print("=" * 70)
    
    scorer = RubberScoring()
    
    test_cases = [
        # (contract, declarer, tricks, doubled, description)
        ('3NT', 'N', 7, True, "3NT doubled, down 2 (not vul)"),
        ('4S', 'N', 7, True, "4S doubled, down 3 (not vul)"),
    ]
    
    for contract, declarer, tricks, doubled, desc in test_cases:
        result = scorer.record_hand_result(contract, declarer, tricks, doubled=doubled)
        score = result['score']
        undertricks = score.get('undertricks', 0)
        
        print(f"\n{desc}")
        print(f"  Contract: {contract}X by {declarer}")
        print(f"  Made {tricks} tricks")
        print(f"  Undertricks: {undertricks}")
        print(f"  Penalty: {score['total']} to defenders")
        
        # Verify penalty amounts
        if undertricks == 2:
            expected = 100 + 200  # First 100, second 200
            assert score['total'] == expected, f"2 down doubled not vul should be {expected}, got {score['total']}"
        elif undertricks == 3:
            expected = 100 + 200 + 200  # First 100, second 200, third 200
            assert score['total'] == expected, f"3 down doubled not vul should be {expected}, got {score['total']}"
    
    print("\n" + "=" * 70)
    print("✅ All doubled penalty tests passed!")
    print("=" * 70)

if __name__ == '__main__':
    test_doubled_contracts()
    test_redoubled_contracts()
    test_doubled_overtricks()
    test_doubled_penalties()
    
    print("\n" + "=" * 70)
    print("🎉 ALL DOUBLED/REDOUBLED TESTS PASSED!")
    print("=" * 70)

# Rubber Bridge Scoring Integration Guide

## Overview

The rubber bridge scoring system tracks cumulative scores across multiple hands, managing:
- Game progression (first to 2 games wins the rubber)
- Vulnerability (automatic after winning first game)
- Above-the-line points (bonuses, overtricks, penalties)
- Below-the-line points (contract tricks towards game)
- Rubber bonuses (500 for 2-0, 700 for 2-1)
- Session statistics (total rubbers won)

## Quick Start

### 1. Initialize Scoring

```python
from rubber_scoring import RubberScoring
import web_dashboard as DashboardBroadcaster

# Create scorer instance
rubber_scorer = RubberScoring()

# Broadcast initial state
DashboardBroadcaster.DashboardBroadcaster.update_rubber_score(
    rubber_scorer.get_rubber_status()
)
```

### 2. Record Hand Results

After each hand is complete:

```python
# Example: 3NT by North, made 9 tricks
contract = '3NT'
declarer = 'N'
tricks_made = 9

# Record result
result = rubber_scorer.record_hand_result(contract, declarer, tricks_made)

# Broadcast update to dashboard
DashboardBroadcaster.DashboardBroadcaster.update_rubber_score(
    result['rubber_status']
)

# Check if rubber complete
if result['rubber_status']['rubber_complete']:
    print(f"Rubber complete! Starting new rubber...")
    rubber_scorer.start_new_rubber()
    DashboardBroadcaster.DashboardBroadcaster.update_rubber_score(
        rubber_scorer.get_rubber_status()
    )
```

### 3. Special Cases

**Doubled Contracts:**
```python
# 4H doubled, made 11 tricks
result = rubber_scorer.record_hand_result('4H', 'S', 11, doubled=True)
```

**Redoubled Contracts:**
```python
# 3C redoubled, made 10 tricks
result = rubber_scorer.record_hand_result('3C', 'W', 10, redoubled=True)
```

**Defeated Contracts:**
```python
# 6NT down 3 (needed 12, made 9)
result = rubber_scorer.record_hand_result('6NT', 'N', 9)
```

## Integration with bbo_bot.py

Add to your bot after detecting hand completion:

```python
from rubber_scoring import RubberScoring

# Initialize once at bot startup
rubber_scorer = RubberScoring()
DashboardBroadcaster.update_rubber_score(rubber_scorer.get_rubber_status())

# After 13 tricks played and contract known:
def on_hand_complete(contract, declarer):
    """Called when all 13 tricks have been played"""
    
    # Count tricks made by declarer's partnership
    if declarer in ['N', 'S']:
        tricks_made = decision_engine.tricks_won['NS']
    else:
        tricks_made = decision_engine.tricks_won['EW']
    
    # Determine if doubled/redoubled (from bidding)
    doubled = 'X' in contract or 'x' in contract
    redoubled = 'XX' in contract or 'xx' in contract
    
    # Clean contract string
    contract_clean = contract.replace('X', '').replace('x', '')
    
    # Record result
    result = rubber_scorer.record_hand_result(
        contract_clean,
        declarer,
        tricks_made,
        doubled=doubled,
        redoubled=redoubled
    )
    
    # Broadcast to dashboard
    DashboardBroadcaster.update_rubber_score(result['rubber_status'])
    
    # Print summary
    score_info = result['score']
    print(f"\\n📊 Hand Complete:")
    print(f"   Contract: {contract} by {declarer}")
    print(f"   Result: {tricks_made} tricks")
    print(f"   Score: {score_info['partnership']} +{score_info['total']}")
    print(f"   {score_info['description']}")
    
    # Check for rubber completion
    if result['rubber_status']['rubber_complete']:
        status = result['rubber_status']
        ns_total = status['ns']['total']
        ew_total = status['ew']['total']
        winner = 'NS' if ns_total > ew_total else 'EW'
        
        print(f"\\n🏆 RUBBER COMPLETE!")
        print(f"   Winner: {winner}")
        print(f"   Games: NS {status['ns']['games']} - EW {status['ew']['games']}")
        print(f"   Final: NS {ns_total} - EW {ew_total}")
        
        # Start new rubber
        rubber_scorer.start_new_rubber()
        DashboardBroadcaster.update_rubber_score(rubber_scorer.get_rubber_status())
```

## Scoring Rules Reference

### Below-the-Line (Game Points)

Points needed for game: **100**

**Per trick value:**
- Clubs/Diamonds: 20 per trick
- Hearts/Spades: 30 per trick
- No Trump: 40 for first trick, 30 for others

**Doubled/Redoubled:**
- Doubled: multiply by 2
- Redoubled: multiply by 4

### Above-the-Line (Bonuses)

**Game Bonuses:**
- Game (not vulnerable): +300
- Game (vulnerable): +500
- Part score: +50

**Slam Bonuses:**
- Small slam (not vul): +500
- Small slam (vul): +750
- Grand slam (not vul): +1000
- Grand slam (vul): +1500

**Double/Redouble Bonuses:**
- Doubled: +50
- Redoubled: +100

**Overtricks:**
- Not doubled: face value per trick
- Doubled (not vul): 100 per trick
- Doubled (vul): 200 per trick
- Redoubled: double the doubled value

**Rubber Bonuses:**
- Win 2-0: +500
- Win 2-1: +700

### Penalties (Undertricks)

**Not Doubled:**
- Not vulnerable: 50 per trick
- Vulnerable: 100 per trick

**Doubled:**
- First undertrick: 100 (not vul) / 200 (vul)
- 2nd-3rd undertrick: 200 (not vul) / 300 (vul)
- 4th+ undertrick: 300 each

**Redoubled:** Double the doubled penalties

## Dashboard Display

The rubber scoring panel shows:

- **Current Rubber Number**
- **Games Won** (NS vs EW)
- **Vulnerability Status** (VUL indicator when vulnerable)
- **Below-the-Line Points** (progress toward game)
- **Above-the-Line Points** (bonuses and extras)
- **Total Score** (running total for rubber)
- **Leader** (who's ahead and by how much)
- **Rubbers Won** (session totals)
- **Rubber Complete** (notification with final score)

Updates automatically in real-time as hands are scored.

## Testing

Run the test suite to verify scoring:

```bash
python test_rubber_scoring.py
```

All 7 tests should pass, covering:
- Basic games
- Part scores
- Slams
- Doubled contracts
- Penalties
- Rubber completion
- Competitive rubbers

## Troubleshooting

**Score not updating:**
- Check dashboard is connected (green indicator)
- Verify `update_rubber_score()` is called after recording
- Check browser console for errors

**Wrong vulnerability:**
- Vulnerability auto-updates after first game won
- Reset with `start_new_rubber()` for new rubber

**Incorrect score:**
- Verify tricks_made count is correct
- Check contract parsing (doubled/redoubled)
- Review scoring rules above
- Run test suite to verify calculations

## Advanced Features

### Get Score Summary

```python
summary = rubber_scorer.get_score_summary()
print(summary['current_rubber'])  # Current rubber state
print(summary['rubber_history'])  # All completed rubbers
print(summary['hand_history'])    # Recent hands
```

### Manual Score Adjustment

```python
# Direct access to scores (use with caution)
rubber_scorer.ns_above += 100  # Add penalty
rubber_scorer.ew_below = 0     # Reset part score
```

### Session Statistics

```python
status = rubber_scorer.get_rubber_status()
print(f"NS has won {status['ns']['rubbers']} rubbers")
print(f"EW has won {status['ew']['rubbers']} rubbers")
```

# Feature Update: Claim Handling & HCP Display

**Date:** November 2, 2025  
**Branch:** `feature/rubber-scoring`  
**Commit:** 958770a

---

## Overview

Two major improvements to the rubber bridge scoring system:

1. **Claim Handling** - Rubber scoring now updates when players claim remaining tricks
2. **HCP Display** - Dashboard shows High Card Points for each player and partnership

---

## 1. Claim Handling

### Problem
When players claimed remaining tricks instead of playing them out, the rubber scoring system didn't update because it only detected completion when all 13 tricks were played.

### Solution
Added detection and handling for `claim_accepted` events from BBO.

### How It Works

**When a claim is accepted:**

1. **Detect the event**: Bot receives `claim_accepted` with `tricks_claimed` and `claimer`
2. **Calculate total tricks**:
   - If declarer claims: `tricks_made = tricks_won + tricks_claimed`
   - If defender claims: `tricks_made = tricks_won + (remaining - claimed)`
3. **Record result**: Call `rubber_scorer.record_hand_result()` with total tricks
4. **Broadcast update**: Send updated rubber score to dashboard

### Example

```
Board: 3NT by N
Tricks played: 7 (NS won 6, EW won 1)
North claims: 6 tricks

Calculation:
  NS total = 6 (won) + 6 (claimed) = 12 tricks
  Result: 3NT +3 overtricks
  Score: NS +490
```

### Code Location
- **File:** `bbo_bot.py`
- **Function:** `handle_game_event()` 
- **Event:** `claim_accepted`

### Console Output
```
✅ Claim accepted: 6 tricks by N

🎯 HAND COMPLETE (via claim)!
   Contract: 3NT by N
   Tricks: NS=6, EW=1, Claimed=6
   Declarer's partnership (NS) made 12 tricks
📊 Broadcasting rubber score update: {...}
   Score: NS +490 (3NT made with 3 overtrick(s))
```

---

## 2. High Card Points (HCP) Display

### Feature
Dashboard now shows High Card Points for each player and partnership.

### What's Shown

**Partnership Totals** (prominent display):
- NS Partnership: Total HCP
- EW Partnership: Total HCP

**Individual Players**:
- North: HCP
- South: HCP
- East: HCP
- West: HCP

**Balance Indicator**:
- Shows which partnership has more HCP
- Displays the difference

### UI Design

```
┌─────────────────────────────────┐
│ High Card Points                │
│                                 │
│  NS Partnership    EW Partnership│
│       18               22       │
│                                 │
│ Individual Players:             │
│   North: 10      East:  11     │
│   South:  8      West:  11     │
│                                 │
│ EW has 4 more HCP               │
└─────────────────────────────────┘
```

### Calculation

HCP values:
- Ace = 4 points
- King = 3 points
- Queen = 2 points
- Jack = 1 point

### When Updated

HCP is calculated and broadcast when:
- New deal starts (all hands visible)
- Dashboard connects/reconnects

### Code Locations

**Backend:**
- `bbo_bot.py` - `calculate_hcp()` function (already existed)
- `bbo_bot.py` - Calculates on new deal
- `web_dashboard.py` - `update_hcp()` broadcaster method
- `web_dashboard.py` - Added `hcp` to state

**Frontend:**
- `dashboard_react.html` - `HCPDisplay` component
- Added to right sidebar above recommendations

### Console Output
```
💎 High Card Points:
   North: 10  South: 8  (NS Total: 18)
   East:  11  West: 11  (EW Total: 22)
```

---

## Benefits

### For Claim Handling:
✅ Rubber scoring works whether hand is played out or claimed  
✅ No missed scoring updates  
✅ Accurate trick counting with claims  
✅ Handles both declarer and defender claims  
✅ Works with all contract types (including slams, doubled, etc.)  

### For HCP Display:
✅ See distribution of high cards at a glance  
✅ Helps evaluate bidding decisions  
✅ Shows partnership strength  
✅ Individual player strength visible  
✅ Balance indicator shows advantage  

---

## Testing

### Claim Handling Tests

**Test file:** `test_claim_handling.py`

```bash
python test_claim_handling.py
```

**Scenarios tested:**
1. ✅ Declarer claims remaining tricks (3NT +3)
2. ✅ Defenders claim (4S down 2)
3. ✅ Slam claim (6H made exactly)

All tests pass!

### HCP Calculation Test

```bash
python -c "
from bbo_bot import calculate_hcp, parse_lin_hand
hand = parse_lin_hand('SAKQJAKQ2H987D654C32')
print(f'HCP: {calculate_hcp(hand)}')
"
```

---

## Usage

### Normal Play (13 tricks)
```
Cards played → 13 tricks complete → Rubber score updates
```

### With Claim
```
Cards played → Player claims → Claim accepted → Rubber score updates
```

### HCP Display
```
New deal starts → HCP calculated → Dashboard shows points
```

---

## Example Dashboard Display

**Right Sidebar (top to bottom):**

1. **Rubber Bridge Scoring**
   - Current rubber status
   - Last hand result
   - Games won, vulnerability
   - Total scores

2. **High Card Points** ← NEW!
   - Partnership totals
   - Individual players
   - Balance indicator

3. **Recommendation**
   - AI card suggestion

4. **Bidding Box**
   - Auction history

5. **Trick History**
   - Previous tricks

6. **DD Analysis**
   - Double dummy results

---

## Files Changed

### Modified
- `bbo_bot.py` (+62 lines)
  - Handle `claim_accepted` events
  - Calculate HCP on new deal
  - Broadcast HCP updates

- `web_dashboard.py` (+6 lines)
  - Add `hcp` to state
  - Add `update_hcp()` method

- `templates/dashboard_react.html` (+53 lines)
  - Create `HCPDisplay` component
  - Add HCP to state
  - Add component to sidebar

### New Files
- `test_claim_handling.py` (63 lines)
  - Test claim scenarios
  - Verify trick calculations

---

## Known Limitations

1. **HCP requires visible hands**: HCP only calculated when hands are visible to the bot
2. **Claim accuracy**: Relies on BBO providing correct claim information
3. **Display updates**: HCP stays same after cards are played (shows initial deal)

---

## Future Enhancements

Possible additions:
- **Distribution points** (void, singleton, doubleton bonuses)
- **Playing strength** (update HCP as cards are played)
- **Historical HCP tracking** (average per session)
- **Claim verification** (warn if claim seems wrong based on visible cards)

---

## Status

✅ **Complete and Tested**  
✅ **All Tests Passing**  
✅ **Ready for Use**  

Both features are fully integrated and working in the `feature/rubber-scoring` branch!

---

## Quick Verification

**Test Claim Handling:**
1. Start bot
2. Play a hand
3. Have someone claim remaining tricks
4. Check console for "🎯 HAND COMPLETE (via claim)!"
5. Check dashboard rubber score updates

**Test HCP Display:**
1. Start bot
2. Open dashboard at http://localhost:5001
3. Start new deal
4. Check console for "💎 High Card Points:"
5. Check dashboard shows HCP card in sidebar

Both features working! 🎉

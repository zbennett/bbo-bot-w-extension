# Decision Engine Documentation

## Overview
The Decision Engine is a core component of the bridge bot that tracks game state and provides optimal play recommendations based on double dummy analysis.

## Architecture

### DecisionEngine Class
Located in `bridge-bot/decision_engine.py`, this class maintains complete game state and provides recommendations.

#### State Tracking
The engine tracks:
- **Board Info**: Board number, dealer, vulnerability
- **Hands**: All four hands in LIN format (SAKQHAKQ...)
- **Auction**: Complete bidding sequence with bidders
- **Contract**: Final contract and declarer/dummy positions
- **Play History**: All played cards with tracking of current trick
- **Trick Count**: NS and EW tricks won
- **Next Player**: Who should play next
- **DD Analysis**: Double dummy results for optimal play

#### Key Methods

##### `reset_deal(board, dealer, vul, hands)`
Resets state for a new deal. Called when a `new_deal` event is received.

**Parameters:**
- `board`: Board number (integer)
- `dealer`: Dealer position ('N', 'S', 'E', or 'W')
- `vul`: Vulnerability string (e.g., "None", "NS", "EW", "Both")
- `hands`: Dictionary mapping N/S/E/W to LIN format hands

##### `update_auction(call, bidder)`
Updates auction state with a new call. Automatically detects when auction is complete (three passes) and determines contract, declarer, dummy, and opening leader.

**Parameters:**
- `call`: The bid/call (e.g., "1S", "P", "X", "XX")
- `bidder`: Who made the call ('N', 'S', 'E', or 'W')

##### `update_card_played(player, card)`
Updates play state with a played card. Tracks the current trick, determines trick winner when complete, and advances to next player.

**Parameters:**
- `player`: Who played the card ('N', 'S', 'E', or 'W')
- `card`: The card played (e.g., "SA", "HK", "D3")

##### `update_dd_analysis(dd_data)`
Stores double dummy analysis results for use in recommendations.

**Parameters:**
- `dd_data`: DD results in BSOL format with tricks dictionary

##### `get_recommendation()`
Returns the optimal card to play for the current player based on DD analysis.

**Returns:**
- `(card, reasoning)`: Tuple with recommended card and explanation
- `(None, reason_string)`: If no recommendation available with explanation

**Examples:**
```python
card, reasoning = engine.get_recommendation()
# ("SA", "Lead from strongest suit (spades) - can make 10 tricks")
# (None, "No double dummy analysis available")
```

##### `get_status_summary()`
Returns a human-readable summary of current game state.

**Returns:** Multi-line string with:
- Board info (number, dealer, vulnerability)
- Contract and declarer (if auction complete)
- Trick count
- Next player and remaining cards
- Current trick in progress

## Integration with Bot

### Event Flow
1. **New Deal**: `handle_game_event('new_deal')` calls `decision_engine.reset_deal()`
2. **Bidding**: `handle_game_event('bid_made')` calls `decision_engine.update_auction()`
3. **Playing**: `handle_game_event('card_played')` calls `decision_engine.update_card_played()`
4. **DD Analysis**: `handle_dd_result()` calls `decision_engine.update_dd_analysis()`

### Recommendation Display
After each card is played, the bot:
1. Calls `decision_engine.get_recommendation()`
2. Displays recommendation with emoji: `💡 Recommendation: ♠A - Lead from strongest suit`
3. Shows reasoning from DD analyzer

## Decision Logic

### Trick Winner Determination
The engine correctly determines trick winners using bridge rules:
- Trump beats non-trump
- Highest card in lead suit wins (if no trump)
- Must follow suit if possible (assumed legal plays from BBO)

### Card Play Recommendations
Uses `DoubleDummyAnalyzer` to:
1. Get remaining cards in current player's hand
2. Analyze DD results for each possible play
3. Recommend card that maximizes trick-taking potential
4. Provide reasoning (e.g., "Lead from strongest suit", "Can make 10 tricks")

### Opening Lead Strategy
When leading to first trick, analyzer considers:
- Which suit provides most tricks
- Avoiding giving away unnecessary tricks
- Creating entries for partner

## Example Usage

```python
from decision_engine import DecisionEngine

# Create engine
engine = DecisionEngine()

# New deal
engine.reset_deal(
    board=1,
    dealer='N',
    vul='None',
    hands={
        'N': 'SAKQHAKQJAKQJAKQ',
        'S': '...',
        'E': '...',
        'W': '...'
    }
)

# Auction
engine.update_auction('1S', 'N')
engine.update_auction('P', 'E')
engine.update_auction('3NT', 'S')
engine.update_auction('P', 'W')
engine.update_auction('P', 'N')
engine.update_auction('P', 'E')  # Auction complete

# Play
engine.update_card_played('E', 'S2')  # Opening lead

# Add DD analysis
engine.update_dd_analysis(dd_data)

# Get recommendation for South
card, reasoning = engine.get_recommendation()
print(f"Play: {card} - {reasoning}")
```

## Testing

### Manual Testing
1. Start bot: `python3 bbo_bot.py`
2. Load Chrome extension
3. Join a BBO game
4. Observe recommendations after each card:
   - Should show "💡 Recommendation: [card]" with reasoning
   - Should only show recommendations when player has turn
   - Should use DD analysis to suggest optimal plays

### Expected Behavior
- ✅ Shows recommendations for each player when it's their turn
- ✅ Recommendations change based on cards remaining
- ✅ Reasoning explains why card is recommended
- ✅ No recommendations during auction (only after play starts)
- ✅ No recommendations if DD analysis not available

## Future Enhancements

### Planned Features
1. **Action Injection**: Send recommended plays back to Chrome extension to automate clicking
2. **Bidding Recommendations**: Use hand evaluation and DD analysis to recommend bids
3. **Learning**: Track success rate of recommendations vs actual results
4. **Multiple Strategies**: Allow choosing between aggressive/conservative play styles

### Possible Improvements
- Cache DD analysis results for better performance
- Pre-calculate all possible plays when turn starts
- Consider opponent's likely holdings based on bidding/play
- Integrate with opening lead databases for statistical guidance

## Troubleshooting

### No Recommendations Showing
**Symptoms:** Cards played but no "💡 Recommendation" messages

**Possible Causes:**
1. DD analysis not received yet (wait for "🧠 DOUBLE DUMMY ANALYSIS" message)
2. Player identification incorrect (check bid_made shows correct seats now)
3. Hand parsing error (verify hands display correctly)

**Debug Steps:**
1. Add logging: `print(f"DEBUG: lead_player={engine.lead_player}, dd_data={engine.dd_data is not None}")`
2. Check `engine.get_status_summary()` shows correct state
3. Verify `_get_remaining_cards()` returns correct cards

### Wrong Recommendations
**Symptoms:** Recommendations don't match optimal play

**Possible Causes:**
1. DD data incorrect or stale
2. Hand state out of sync (missed a card played event)
3. Trick winner calculation wrong

**Debug Steps:**
1. Verify DD data matches hands: Compare `dd_data['tricks']` to manual calculation
2. Check played cards list: Print `engine.played_cards` to verify complete history
3. Test trick winner logic: Create unit tests with known scenarios

### Performance Issues
**Symptoms:** Slow recommendations or lag

**Solutions:**
1. Cache DD analyzer instance instead of creating new one each time
2. Pre-calculate recommendations when DD data received
3. Optimize card parsing and hand tracking

## Code References

### Related Modules
- `dd_analyzer.py`: DoubleDummyAnalyzer class for parsing DD results
- `bbo_bot.py`: Main bot integrating decision engine
- `bbov3.js`: Chrome extension sending game events

### Key Functions
- `DoubleDummyAnalyzer.analyze_position()`: Core recommendation logic
- `_determine_trick_winner()`: Bridge trick rules implementation
- `_get_remaining_cards()`: Hand tracking with played card removal

### Message Formats
See `DATA_STRUCTURES.md` for complete event format documentation.

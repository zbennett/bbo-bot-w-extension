# Bridge Bot Combined - Architecture Overview

## Project Structure

This project consists of two main components:

### 1. **Chrome Extension (zb-bbo/)** 
A modified version of the BBO Helper Chrome extension that runs inside the BridgeBase Online (BBO) website.

### 2. **Python Bot (bridge-bot/)**
A Python WebSocket server (`bbo_bot.py`) that receives game state from the extension and displays it.

---

## How It Works

### Data Flow

```
BridgeBase Website 
    ↓ (WebSocket intercept)
Chrome Extension 
    ↓ (WebSocket on localhost:8675)
Python Bot (bbo_bot.py)
    ↓ (Display in terminal)
```

### Key Files

#### Chrome Extension (zb-bbo/)
- **`bbov3.js`** - Main content script
  - Intercepts BBO WebSocket traffic
  - Tracks game state in `app` object
  - Sends data to Python bot via WebSocket
  
- **`injectedsniffers.js`** - Injected early to intercept WebSocket
  - Extends native WebSocket class
  - Captures all BBO server messages
  
- **`injectedbbo.js`** - Additional injected code
  - Auto-alerts functionality
  - Chat improvements
  
- **`common.js`** - Shared utilities
  - Contains `doubledummy()` function
  - Makes requests to Bridge Solver Online (BSOL) API
  - Caches double dummy results

#### Python Bot (bridge-bot/)
- **`bbo_bot.py`** - WebSocket server
  - Listens on localhost:8675
  - Receives game updates from extension
  - Parses and displays cards in terminal
  - Shows HCP (High Card Points)
  - Displays double dummy analysis

---

## Communication Protocol

### WebSocket Messages Sent to Python Bot

#### 1. **app_update** (sent on every state change)
```javascript
{
  "type": "app_update",
  "app": {
    "deal": {
      "board": "1",
      "d": {
        "hand": ["S.AKQ.KQJ.AKQJT", ...],  // 4 hands in dot notation
        "dealer": "N",
        "vul": "None"
      },
      "play": ["S2", "H3", ...],  // cards played
      "auction": ["1C", "p", "1H", ...],
      "south": "SAKQHKQJDKQJCAKQJT",  // LIN format
      "west": "...",
      "north": "...",
      "east": "..."
    },
    "table": {
      "players": ["South", "West", "North", "East"],
      "table_id": "12345",
      "style": "t-pairs",  // tournament type
      "type": "7"
    }
  }
}
```

#### 2. **double_dummy** (DD analysis results)
```javascript
{
  "type": "double_dummy",
  "dd": {
    "cNS": "3NT",      // optimal contract for NS
    "cEW": "4S",       // optimal contract for EW
    "sNS": 400,        // score for NS
    "sEW": -400,       // score for EW
    "tricks": {
      "N": {"S": 9, "H": 8, "D": 7, "C": 10, "N": 9},  // tricks for each seat/strain
      "S": {...},
      "E": {...},
      "W": {...}
    }
  }
}
```

#### 3. **card_played** (individual card events)
```javascript
{
  "type": "card_played",
  "card": "S2"
}
```

---

## Current Issues & Inefficiencies

### 1. **Sending Entire App Object**
Currently, the extension sends the entire `app` object on every change:
```javascript
function processWebsocket(e) {
    console.info(app);
    if (app && app.deal && app.deal.d) {
        doubledummy(app.deal.d, pref.appDoubleDummyMode === 'ondemand', zacharyDDcallback);
    }
    sendAppToPython(app)  // ← Sends everything!
}
```

**Problem**: Most of `app` doesn't change between updates (table info, player names, etc.)

**Better approach**: Send only deltas or specific events

### 2. **Double Dummy Requests**
The extension requests DD analysis from BSOL (Bridge Solver Online):
```javascript
// In common.js line ~2360
async function doubledummy(d, bCacheOnly, callback, bWaitResolve=false) {
    // Makes HTTP request to John Goacher's BSOL
    // https://dds.bridgewebs.com/...
    // Caches results in app.pendingDD
}
```

**Flow**:
1. Extension gets deal from BBO
2. Extension requests DD from BSOL API
3. Extension receives DD results
4. Extension sends DD to Python bot via `zacharyDDcallback()`

### 3. **Key BBO Messages Tracked**

The extension intercepts these server messages:
- `<sc_deal>` - New deal/board
- `<sc_call_made>` - Bid made
- `<sc_card_played>` - Card played  
- `<sc_claim_accepted>` - Claim accepted
- `<sc_player_sit>` - Player seated
- `<sc_board_details>` - Full hand details
- `<sc_dummy_holds>` - Dummy's hand revealed

---

## Game State in Python Bot

### Current Display
```
📣 Double Dummy Result: 3NT (Score: 400)

                    North (HCP: 12)
              ♠: AKQ
              ♥: 876
              ♦: KQJ
              ♣: 543

West (HCP: 8)                         East (HCP: 10)
♠: 54                                 ♠: 876
♥: QJ9                                ♥: T432
♦: 876                                ♦: T9
♣: KQJ98                              ♣: AT76

                    South (HCP: 10)
              ♠: JT932
              ♥: AK5
              ♦: A432
              ♣: 2
```

### Card Tracking
- Parses LIN format (e.g., "SAKQHKQJ...")
- Removes played cards from hands
- Calculates HCP for each seat

---

## Next Steps for Automation

### Phase 1: Enhance Information Flow
1. **Send structured events instead of full app**
   ```javascript
   // New event types:
   { type: "deal_start", board: 1, dealer: "N", vul: "None", hands: [...] }
   { type: "bid_made", call: "1C", seat: "South", time: 1234 }
   { type: "card_played", card: "S2", seat: "West", legal: [...] }
   ```

2. **Add legal move information**
   - BBO knows valid bids/plays
   - Send this to bot for validation

### Phase 2: Decision Making
1. **Implement bridge logic in Python**
   - Parse double dummy to find best line
   - Consider vulnerability, scoring
   - Handle common bidding systems (SAYC, 2/1)

2. **Add bidding logic**
   ```python
   def choose_bid(hand, auction, vul, dd_analysis):
       # Analyze hand strength
       # Apply bidding system rules
       # Use DD to optimize contract
       return best_bid
   ```

3. **Add play logic**
   ```python
   def choose_card(hand, dummy, played_cards, contract, dd_analysis):
       # Use DD to find best card
       # Consider which cards are still out
       # Follow suit rules
       return best_card
   ```

### Phase 3: Automation
1. **Send commands back to extension**
   - Reverse WebSocket: Python → Extension
   - Extension simulates clicks on BBO interface
   
2. **Inject decisions into BBO**
   ```javascript
   // In extension
   socket.onmessage = (event) => {
       const msg = JSON.parse(event.data);
       if (msg.type === "make_bid") {
           clickBidButton(msg.call);
       }
       if (msg.type === "play_card") {
           clickCard(msg.card);
       }
   }
   ```

---

## Technical Considerations

### WebSocket Connection
- Currently one-way (Extension → Python)
- Need bidirectional for automation
- Port 8675 (falls back if in use)

### BBO UI Interaction
- Would need to simulate clicks
- Must respect timing (look human)
- Handle UI variations

### Rate Limiting & Detection
- BBO may detect automated play
- Need to add randomness to timing
- Consider ethical implications

### Double Dummy Solvers
- Current: Uses online BSOL API
- Could use local DD solver (DDS library)
- Python wrapper: `python-dds` or `endplay`

---

## File Reference

### Extension Entry Points
- `manifest.json` - Extension configuration
- `bbov3early.js` - Injected at document_start (WebSocket intercept)
- `bbov3.js` - Main content script at document_end
- `service.js` - Background service worker (Manifest V3)

### Key Constants
```javascript
SEAT_ORDER = ["South", "West", "North", "East"]  // BBO order
SUITS = ['S', 'H', 'D', 'C']
```

### Python Bot Constants
```python
SEAT_ORDER = ["South", "West", "North", "East"]
SUITS = ['S', 'H', 'D', 'C']
POINTS = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
```

---

## Resources

- **BBO WebSocket Protocol**: Reverse engineered, not officially documented
- **Bridge Solver Online**: https://dds.bridgewebs.com/
- **DDS (Double Dummy Solver)**: https://github.com/dds-bridge/dds
- **Bridge rules**: Standard American, 2/1 Game Force

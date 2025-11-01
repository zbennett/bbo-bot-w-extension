# Quick Start Guide

## Understanding Your Current Setup

You have a working system that:
1. ✅ Chrome extension captures BBO game state
2. ✅ WebSocket sends data to Python bot
3. ✅ Python displays cards and double dummy results

## Running the Current System

### Terminal 1: Start Python Bot
```bash
cd /Users/zbennett/git/bridge-bot-combined/bridge-bot
python3 bbo_bot.py
```

You should see:
```
🚀 Server running at ws://localhost:8675
```

### Terminal 2: Load Chrome Extension

1. Open Chrome
2. Go to `chrome://extensions`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select: `/Users/zbennett/git/bridge-bot-combined/zb-bbo`

### Terminal 3: Test on BBO

1. Go to https://www.bridgebase.com
2. Log in
3. Start playing or watching a game
4. Watch Terminal 1 for output!

---

## What You'll See

### When a new deal starts:
```
✅ WebSocket client connected.

              North (HCP: 12)
        ♠: AKQ
        ♥: 876
        ♦: KQJ
        ♣: 543

West (HCP: 8)              East (HCP: 10)
♠: 54                      ♠: 876
♥: QJ9                     ♥: T432
...
```

### When double dummy arrives:
```
📣 Double Dummy Result: 3NT (Score: 400)
```

### When a card is played:
```
S2 played by South after 2.341 sec
```

---

## Next: Make It Better

### Step 1: Improve Data Flow (Recommended First Step)

Instead of sending the entire `app` object every time, let's send specific events.

#### Edit: `zb-bbo/bbov3.js`

Find this line (around line 632):
```javascript
function processWebsocket(e) {
    console.info(app);
    if (app && app.deal && app.deal.d) doubledummy(app.deal.d, pref.appDoubleDummyMode === 'ondemand', zacharyDDcallback);
    sendAppToPython(app)
```

Add this new function before `processWebsocket`:
```javascript
function sendGameEvent(eventType, data) {
    if (socket.readyState === WebSocket.OPEN) {
        const message = {
            type: eventType,
            timestamp: Date.now(),
            data: data
        };
        socket.send(JSON.stringify(message));
        console.log('📤 Sent event:', eventType);
    }
}
```

Now modify `processWebsocket` to send specific events:
```javascript
function processWebsocket(e) {
    const msg = e.detail.msg;
    const mtype = msg.startsWith('<') ? msg.slice(1, msg.search(' ')) : 
                  msg.slice(0, msg.search('\x01'));
    
    console.info(app);
    
    // Send specific events instead of full app
    if (mtype === 'sc_deal' && app.deal) {
        sendGameEvent('new_deal', {
            board: app.deal.board,
            dealer: app.deal.dealer,
            vul: app.deal.vul,
            hands: {
                south: app.deal.south,
                west: app.deal.west,
                north: app.deal.north,
                east: app.deal.east
            }
        });
    }
    else if (mtype === 'sc_call_made') {
        let call = msg.match( /(?<= call=")\w+(?=")/ )[0];
        sendGameEvent('bid_made', {
            call: call,
            auction: app.deal.auction
        });
    }
    else if (mtype === 'sc_card_played') {
        let card = msg.match( /(?<= card=")[CDHS][2-9TJQKA](?=")/ )[0];
        sendGameEvent('card_played', {
            card: card,
            played: app.deal.play
        });
    }
    
    // Keep DD as before
    if (app && app.deal && app.deal.d) {
        doubledummy(app.deal.d, pref.appDoubleDummyMode === 'ondemand', zacharyDDcallback);
    }
    
    // Still send full app for now (can remove later)
    sendAppToPython(app);
}
```

#### Edit: `bridge-bot/bbo_bot.py`

Add event handling:
```python
async def handle_connection(websocket):
    print("✅ WebSocket client connected.")
    async for message in websocket:
        try:
            data = json.loads(message)
            event_type = data.get("type")
            
            if event_type == "new_deal":
                print("\n" + "="*50)
                print(f"🎲 NEW DEAL - Board {data['data']['board']}")
                print(f"   Dealer: {data['data']['dealer']}, Vul: {data['data']['vul']}")
                print("="*50)
                
            elif event_type == "bid_made":
                auction = data['data']['auction']
                print(f"📢 Auction: {' '.join(auction)}")
                
            elif event_type == "card_played":
                card = data['data']['card']
                print(f"🃏 Card played: {card}")
                
            elif event_type == "double_dummy":
                dd = data.get("dd")
                print(f"🧠 Double Dummy: {dd.get('cNS')} (Score: {dd.get('sNS')})")
                sendDDToPython(dd)
                
            elif event_type == "app_update":
                # Old format - still process
                app = data.get("app")
                analyze_app(app)
                
        except Exception as e:
            print("❌ Error:", e)
            import traceback
            traceback.print_exc()
```

### Test It

1. Reload extension in Chrome
2. Restart Python bot
3. Play a hand on BBO
4. You should see specific events now:

```
📤 Sent event: new_deal
🎲 NEW DEAL - Board 1
   Dealer: N, Vul: None
==================================================

📤 Sent event: bid_made  
📢 Auction: 1C

📤 Sent event: card_played
🃏 Card played: S2
```

---

## Step 2: Add Basic Decision Logic

Create a new file `bridge-bot/simple_ai.py`:

```python
"""Simple AI for making bridge decisions"""

def evaluate_hand(hand):
    """Calculate HCP"""
    points = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    hcp = 0
    for card in hand:
        if len(card) == 2:
            hcp += points.get(card[1], 0)
    return hcp

def suggest_opening_bid(hand_str):
    """
    Suggest an opening bid
    hand_str: e.g., "SAKQJHAKQJDAKQJCAKQJ"
    """
    # Parse hand
    suits = {'S': [], 'H': [], 'D': [], 'C': []}
    current_suit = None
    
    for char in hand_str:
        if char in 'SHDC':
            current_suit = char
        else:
            suits[current_suit].append(char)
    
    # Convert to cards
    hand = []
    for suit, ranks in suits.items():
        for rank in ranks:
            hand.append(suit + rank)
    
    hcp = evaluate_hand(hand)
    
    # Count suit lengths
    lengths = {s: len(r) for s, r in suits.items()}
    
    # Simple opening logic
    if hcp < 12:
        return "Pass", f"Only {hcp} HCP"
    
    if hcp >= 15 and hcp <= 17:
        # Check balanced
        sorted_lengths = sorted(lengths.values())
        if sorted_lengths == [2, 3, 4, 4] or sorted_lengths == [3, 3, 3, 4]:
            return "1NT", f"{hcp} HCP, balanced"
    
    # Open longest suit
    longest_suit = max(lengths, key=lengths.get)
    longest_length = lengths[longest_suit]
    
    if longest_length >= 5:
        return f"1{longest_suit}", f"{hcp} HCP, {longest_length} {longest_suit}"
    
    # Default: better minor
    if lengths['D'] >= lengths['C']:
        return "1D", f"{hcp} HCP, better minor"
    else:
        return "1C", f"{hcp} HCP, better minor"

# Test it
if __name__ == "__main__":
    # Test with a strong balanced hand
    test_hand = "SAKQHAKQDAKQCAKQ"
    bid, reason = suggest_opening_bid(test_hand)
    print(f"Suggested bid: {bid}")
    print(f"Reason: {reason}")
```

Test it:
```bash
python3 simple_ai.py
```

### Integrate with Bot

Update `bbo_bot.py`:

```python
from simple_ai import suggest_opening_bid

async def handle_connection(websocket):
    print("✅ WebSocket client connected.")
    
    current_hand = None
    
    async for message in websocket:
        try:
            data = json.loads(message)
            event_type = data.get("type")
            
            if event_type == "new_deal":
                deal_data = data['data']
                current_hand = deal_data['hands']['south']
                
                # Suggest opening bid if dealer
                if deal_data['dealer'] == 'S':
                    bid, reason = suggest_opening_bid(current_hand)
                    print(f"\n🤖 AI Suggestion: {bid}")
                    print(f"   Reasoning: {reason}")
                
            # ... rest of code ...
```

Now when you're dealer, the bot will suggest a bid!

---

## Step 3: Use Double Dummy for Card Play

Create `bridge-bot/play_ai.py`:

```python
"""Use double dummy to suggest best card"""

def suggest_card(hand, dd_tricks, contract):
    """
    Suggest best card to play based on DD
    
    Args:
        hand: List of cards we hold
        dd_tricks: Double dummy trick table
        contract: Current contract (e.g., "3NT")
    
    Returns:
        card, reason
    """
    if not dd_tricks:
        # No DD available, play highest card
        return hand[0], "No DD - playing high"
    
    # Extract contract info
    strain = contract[-1]  # S, H, D, C, or N
    
    # For now, simple logic: look at tricks available
    # In real implementation, would simulate each card
    
    # Group by suit
    by_suit = {}
    for card in hand:
        suit = card[0]
        if suit not in by_suit:
            by_suit[suit] = []
        by_suit[suit].append(card)
    
    # Play from longest suit (simple heuristic)
    longest_suit = max(by_suit, key=lambda s: len(by_suit[s]))
    best_card = by_suit[longest_suit][0]
    
    return best_card, f"Playing from longest suit {longest_suit}"

# Test
if __name__ == "__main__":
    hand = ['SA', 'SK', 'SQ', 'H2', 'H3']
    dd = {'tricks': {'S': {'N': 9}}}
    
    card, reason = suggest_card(hand, dd, "3NT")
    print(f"Suggested card: {card}")
    print(f"Reason: {reason}")
```

---

## Debugging Tips

### See Extension Console
1. Go to `chrome://extensions`
2. Find "BBO Helper" extension
3. Click "Inspect views: service worker" (for background)
4. Open BBO website
5. Press F12 for page console
6. Filter by "BBO Helper" or "Zach"

### See WebSocket Traffic
In extension console:
```javascript
// See what's being sent
console.log(socket.readyState);  // Should be 1 (OPEN)
```

### Python Debug Mode
Add to `bbo_bot.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Save Game State
Add to Python bot:
```python
import json

async def handle_connection(websocket):
    game_log = []
    
    async for message in websocket:
        data = json.loads(message)
        game_log.append(data)
        
        # Save every 10 events
        if len(game_log) % 10 == 0:
            with open('game_log.json', 'w') as f:
                json.dump(game_log, f, indent=2)
```

---

## Common Issues

### WebSocket Won't Connect
- Check port 8675 isn't in use: `lsof -i :8675`
- Try different port in both extension and Python
- Check firewall settings

### Extension Not Loading
- Check `manifest.json` is valid
- Look for errors in `chrome://extensions`
- Make sure all JS files are present

### No Data Received
- Open BBO website console (F12)
- Look for "WebSocket" errors
- Verify `socket.readyState === 1`

### Double Dummy Not Working
- Check internet connection (needs BSOL API)
- Look for CORS errors
- Verify deal format is correct

---

## What's Next?

After you've tested the improvements above:

1. **Read** `ROADMAP.md` for full development plan
2. **Review** `DATA_STRUCTURES.md` to understand data formats
3. **Implement** Phase 2: Better decision logic
4. **Consider** ethics and BBO terms of service

---

## Getting Help

Questions to ask yourself:
- What part of the codebase do I not understand?
- What specific feature do I want to add next?
- Am I testing in practice mode or real games?

Remember: Always test in practice/casual games first!

# Bridge Bot Development Roadmap

## Current State ✅
- Chrome extension intercepts BBO game state
- WebSocket sends data to Python bot
- Python bot displays cards and double dummy results
- Both systems understand the game state

## Goal 🎯
Create an automated bridge player that:
1. Analyzes the current game state
2. Uses double dummy analysis to determine optimal play
3. Makes decisions for bidding and card play
4. Eventually automates the entire playing process

---

## Phase 1: Optimize Data Transfer (Week 1)

### Problems to Fix
1. **Sending entire `app` object is wasteful**
2. **No clear event structure**
3. **Python can't tell what changed**

### Implementation

#### Step 1.1: Create Event-Based Messages (Extension)
**File**: `zb-bbo/bbov3.js`

Replace the blanket `sendAppToPython(app)` with specific events:

```javascript
// Add after line 632 in bbov3.js
function sendEventToPython(eventType, data) {
    if (socket.readyState === WebSocket.OPEN) {
        const message = {
            type: eventType,
            timestamp: Date.now(),
            data: data
        };
        socket.send(JSON.stringify(message));
    }
}

function processWebsocket(e) {
    const msg = e.detail.msg;
    const mtype = msg.startsWith('<') ? msg.slice(1, msg.search(' ')) : msg.slice(0, msg.search('\x01'));
    
    if (mtype === 'sc_deal') {
        // New deal started
        const deal = parseDeal(msg);
        sendEventToPython('deal_start', {
            board: deal.board,
            dealer: deal.dealer,
            vul: deal.vul,
            hands: deal.hands,
            table_id: deal.table_id
        });
    }
    else if (mtype === 'sc_call_made') {
        // Bid made
        let call = msg.match( /(?<= call=")\w+(?=")/ )[0];
        sendEventToPython('bid_made', {
            call: call,
            auction: app.deal.auction
        });
    }
    else if (mtype === 'sc_card_played') {
        // Card played
        let card = msg.match( /(?<= card=")[CDHS][2-9TJQKA](?=")/ )[0];
        sendEventToPython('card_played', {
            card: card,
            trick: app.trick,
            played: app.deal.play
        });
    }
    
    // Still keep app state for reference
    console.info(app);
}
```

#### Step 1.2: Handle Events in Python
**File**: `bridge-bot/bbo_bot.py`

```python
import asyncio
import websockets
import json
from datetime import datetime

class BridgeGameState:
    """Maintains current game state"""
    def __init__(self):
        self.board = None
        self.dealer = None
        self.vul = None
        self.hands = {}
        self.auction = []
        self.played_cards = []
        self.current_trick = []
        self.dd_analysis = None
        
    def update_from_deal(self, data):
        """Process new deal"""
        self.board = data['board']
        self.dealer = data['dealer']
        self.vul = data['vul']
        self.hands = parse_hands(data['hands'])
        self.auction = []
        self.played_cards = []
        print(f"\n🎲 New Deal - Board {self.board}")
        print(f"   Dealer: {self.dealer}, Vul: {self.vul}")
        display_hands(self.hands)
        
    def update_from_bid(self, data):
        """Process bid"""
        self.auction = data['auction']
        print(f"\n📢 Auction: {' '.join(self.auction)}")
        
    def update_from_card(self, data):
        """Process card play"""
        card = data['card']
        self.played_cards = data['played']
        self.current_trick = data['trick']['cards']
        print(f"\n🃏 Card played: {card}")
        print(f"   Current trick: {self.current_trick}")
        
    def update_dd(self, dd_data):
        """Store double dummy results"""
        self.dd_analysis = dd_data
        print(f"\n🧠 Double Dummy: {dd_data.get('cNS')} (NS: {dd_data.get('sNS')})")

# Global game state
game = BridgeGameState()

async def handle_connection(websocket):
    print("✅ WebSocket client connected.")
    async for message in websocket:
        try:
            data = json.loads(message)
            event_type = data.get("type")
            
            if event_type == "deal_start":
                game.update_from_deal(data['data'])
                
            elif event_type == "bid_made":
                game.update_from_bid(data['data'])
                
            elif event_type == "card_played":
                game.update_from_card(data['data'])
                
            elif event_type == "double_dummy":
                game.update_dd(data.get("dd"))
                
            elif event_type == "app_update":
                # Fallback for old format
                print("⚠️  Received legacy app_update")
                
        except Exception as e:
            print("❌ Error:", e)
            import traceback
            traceback.print_exc()
```

---

## Phase 2: Add Decision Logic (Week 2-3)

### Step 2.1: Parse Double Dummy for Best Play

```python
# bridge-bot/dd_analyzer.py

class DoubleDummyAnalyzer:
    """Analyze double dummy results to find best play"""
    
    def __init__(self, dd_data):
        self.dd = dd_data
        self.tricks = dd_data.get('tricks', {})
        
    def best_card_for_declarer(self, hand, legal_cards, contract):
        """
        Find the best card to play as declarer
        
        Args:
            hand: Current hand (list of cards)
            legal_cards: Cards that can legally be played
            contract: Current contract (e.g., "3NT")
        
        Returns:
            best_card: The optimal card to play
            explanation: Why this card is best
        """
        strain = contract[-1]  # N, S, H, D, C
        declarer_seat = self.get_declarer_seat()
        
        # Get tricks available with each card
        card_scores = {}
        for card in legal_cards:
            # Look up in DD table how many tricks if we play this card
            # This requires more complex DD lookup with partial game state
            tricks = self.simulate_card(card, strain, declarer_seat)
            card_scores[card] = tricks
            
        best_card = max(card_scores, key=card_scores.get)
        best_tricks = card_scores[best_card]
        
        explanation = f"Playing {best_card} wins {best_tricks} tricks"
        return best_card, explanation
        
    def best_defense_card(self, hand, legal_cards, contract):
        """Find best defensive card"""
        # Similar logic but minimize declarer's tricks
        pass
```

### Step 2.2: Add Bidding Logic

```python
# bridge-bot/bidding.py

class BiddingSystem:
    """Implement Standard American or 2/1 bidding"""
    
    def __init__(self, system="SAYC"):
        self.system = system
        
    def evaluate_hand(self, hand):
        """Calculate HCP and distribution"""
        hcp = sum(self.point_count(card) for card in hand)
        
        suits = {'S': [], 'H': [], 'D': [], 'C': []}
        for card in hand:
            suits[card[0]].append(card)
            
        distribution = {s: len(cards) for s, cards in suits.items()}
        
        return {
            'hcp': hcp,
            'distribution': distribution,
            'longest_suit': max(distribution, key=distribution.get)
        }
        
    def opening_bid(self, hand, seat, vul):
        """Determine opening bid"""
        eval = self.evaluate_hand(hand)
        
        if eval['hcp'] < 12:
            return 'Pass'
            
        if eval['hcp'] >= 15 and eval['hcp'] <= 17:
            # Check for balanced
            if self.is_balanced(eval['distribution']):
                return '1NT'
                
        # Open longest suit
        longest = eval['longest_suit']
        if eval['distribution'][longest] >= 5:
            return f"1{longest}"
            
        # 4-card majors, better minor
        if eval['distribution']['H'] == 4:
            return '1H'
        if eval['distribution']['S'] == 4:
            return '1S'
            
        # Better minor
        if eval['distribution']['D'] >= eval['distribution']['C']:
            return '1D'
        return '1C'
```

### Step 2.3: Integrate Decision Making

```python
# bridge-bot/bot_player.py

class BridgeBot:
    """Main bot that makes decisions"""
    
    def __init__(self):
        self.game = BridgeGameState()
        self.bidding = BiddingSystem("SAYC")
        self.dd_analyzer = None
        
    def decide_bid(self):
        """Decide what to bid"""
        my_hand = self.game.hands['South']  # Assuming we're South
        my_seat = 'South'
        
        if len(self.game.auction) == 0:
            # We're opening
            bid = self.bidding.opening_bid(
                my_hand, 
                my_seat, 
                self.game.vul
            )
        else:
            # Responding or competing
            bid = self.bidding.respond_to_auction(
                my_hand,
                self.game.auction,
                self.game.vul
            )
            
        print(f"\n🤖 Bot decision: {bid}")
        return bid
        
    def decide_card(self):
        """Decide which card to play"""
        my_hand = self.game.hands['South']
        legal_cards = self.get_legal_cards(my_hand)
        
        if self.dd_analyzer:
            card, reason = self.dd_analyzer.best_card_for_declarer(
                my_hand,
                legal_cards,
                self.game.contract
            )
        else:
            # Fallback without DD
            card = self.simple_card_choice(my_hand, legal_cards)
            reason = "No DD available, using heuristic"
            
        print(f"\n🤖 Bot plays: {card} - {reason}")
        return card
```

---

## Phase 3: Bidirectional Communication (Week 4)

### Step 3.1: Add Python → Extension Messages

```python
# In bbo_bot.py

async def handle_connection(websocket):
    global current_websocket
    current_websocket = websocket
    
    print("✅ WebSocket client connected.")
    async for message in websocket:
        # ... handle incoming messages ...
        
        # When bot makes decision
        if bot_should_act():
            decision = bot.decide_bid() if in_auction else bot.decide_card()
            await send_to_extension(websocket, decision)

async def send_to_extension(websocket, decision):
    """Send decision back to extension"""
    message = {
        'type': 'bot_action',
        'action': decision['type'],  # 'bid' or 'play'
        'value': decision['value']    # '1NT' or 'SA'
    }
    await websocket.send(json.dumps(message))
```

### Step 3.2: Handle Bot Actions in Extension

```javascript
// In bbov3.js

socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    if (msg.type === 'bot_action') {
        if (msg.action === 'bid') {
            makeBid(msg.value);
        } else if (msg.action === 'play') {
            playCard(msg.value);
        }
    }
};

function makeBid(call) {
    // Find the bid button and click it
    const bidButton = findBidButton(call);
    if (bidButton) {
        // Add slight random delay to look human
        setTimeout(() => {
            bidButton.click();
            console.log('🤖 Bot bid:', call);
        }, Math.random() * 1000 + 500);
    }
}

function playCard(card) {
    // Find the card element and click it
    const cardElement = findCardInHand(card);
    if (cardElement) {
        setTimeout(() => {
            cardElement.click();
            console.log('🤖 Bot played:', card);
        }, Math.random() * 2000 + 1000);
    }
}

function findBidButton(call) {
    // BBO UI has buttons for each bid
    // Need to inspect BBO DOM to find correct selectors
    const buttons = document.querySelectorAll('.biddingBoxButtonClass');
    for (let btn of buttons) {
        if (btn.innerText === call) {
            return btn;
        }
    }
    return null;
}
```

---

## Phase 4: Safety & Testing (Week 5-6)

### Step 4.1: Add Safety Features

```python
# bridge-bot/safety.py

class BotSafety:
    """Prevent detection and errors"""
    
    def __init__(self):
        self.human_timing_min = 2.0  # seconds
        self.human_timing_max = 15.0
        self.last_action_time = 0
        
    def should_act_now(self):
        """Add human-like hesitation"""
        elapsed = time.time() - self.last_action_time
        
        # Don't act instantly
        if elapsed < self.human_timing_min:
            return False
            
        # Add randomness
        if random.random() < 0.3:  # 30% chance to wait longer
            return False
            
        return True
        
    def add_thinking_time(self):
        """Random delay before action"""
        # Longer for complex decisions
        base_delay = random.uniform(2, 5)
        thinking_delay = random.gauss(3, 1)  # Normal distribution
        return max(base_delay, thinking_delay)
```

### Step 4.2: Testing Mode

```python
# Add flag to enable manual verification

class BridgeBot:
    def __init__(self, auto_play=False):
        self.auto_play = auto_play
        
    def decide_bid(self):
        bid = self.calculate_bid()
        
        if not self.auto_play:
            print(f"\n🤖 Suggested bid: {bid}")
            confirm = input("   Execute? (y/n): ")
            if confirm.lower() != 'y':
                return None
                
        return bid
```

---

## Testing Strategy

### Level 1: Practice Mode
- Test in BBO practice tables
- Use "Play with robots" mode
- Verify decisions are reasonable

### Level 2: Bidding Only
- Bot bids, human plays
- Check for system violations
- Verify DD integration works

### Level 3: Playing Only  
- Human bids, bot plays
- Use DD to follow optimal line
- Verify card selection logic

### Level 4: Full Automation
- Bot handles everything
- Monitor for errors
- Add logging for debugging

---

## Ethical Considerations

### Important Notes
1. **BBO Terms of Service**: Automated play may violate ToS
2. **Fair Play**: Using bots in competitive games is cheating
3. **Recommended Uses**:
   - Personal practice/learning
   - Testing bridge theory
   - Research purposes
   - Always disclose bot use to opponents

### Suggested Disclaimers
- Add "-BOT" suffix to username
- Only play in casual/practice games
- Document that this is educational

---

## Next Immediate Steps

1. **This Week**: Implement Phase 1 (event-based messaging)
2. **Test**: Verify data flow is cleaner
3. **Next Week**: Start Phase 2 (basic decision logic)

## Questions to Consider

1. Which bidding system to implement first? (SAYC, 2/1, Precision)
2. How sophisticated should play logic be initially?
3. Use online DD API or local solver?
4. What level of automation do you want (advisor vs full auto)?

Let me know which direction you'd like to go first!

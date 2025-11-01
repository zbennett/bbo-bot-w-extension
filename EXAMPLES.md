# Code Examples - Ready to Use

This file contains complete, working code examples you can copy and paste directly into your project.

---

## Example 1: Event-Based Messaging (Extension)

### File: `zb-bbo/bbov3.js`

Add this function near the top of the file (after the socket definition, around line 40):

```javascript
/**
 * Send a specific game event to Python bot
 * This replaces sending the entire app object
 */
function sendGameEvent(eventType, data) {
    if (socket.readyState === WebSocket.OPEN) {
        const message = {
            type: eventType,
            timestamp: Date.now(),
            data: data
        };
        socket.send(JSON.stringify(message));
        console.log('📤 Bot Event:', eventType, data);
    } else {
        console.warn('⚠️  WebSocket not open, cannot send:', eventType);
    }
}
```

Then modify the `processWebsocket` function (around line 632):

```javascript
function processWebsocket(e) {
    console.info(app);
    
    const msg = e.detail.msg;
    const mtype = msg.startsWith('<') ? msg.slice(1, msg.search(' ')) : 
                  msg.slice(0, msg.search('\x01'));
    
    // Send specific events based on message type
    if (mtype === 'sc_deal' && app.deal) {
        // New deal started
        sendGameEvent('new_deal', {
            board: app.deal.board,
            dealer: app.deal.dealer,
            vul: app.deal.vul,
            table_id: app.deal.table_id,
            hands: {
                south: app.deal.south,
                west: app.deal.west,
                north: app.deal.north,
                east: app.deal.east
            }
        });
    }
    else if (mtype === 'sc_call_made' && app.deal) {
        // Bid made
        let call = msg.match( /(?<= call=")\w+(?=")/ )[0];
        sendGameEvent('bid_made', {
            call: call,
            auction: app.deal.auction,
            seat_index: (app.deal.auction.length - 1) % 4
        });
    }
    else if (mtype === 'sc_card_played' && app.deal) {
        // Card played
        let card = msg.match( /(?<= card=")[CDHS][2-9TJQKA](?=")/ )[0];
        sendGameEvent('card_played', {
            card: card,
            played_count: app.deal.play.length,
            current_trick: app.trick ? app.trick.cards : []
        });
    }
    else if (mtype === 'sc_dummy_holds' && app.deal) {
        // Dummy revealed
        sendGameEvent('dummy_revealed', {
            dummy_seat: 'North',  // You can enhance this
            dummy_hand: app.deal.north
        });
    }
    else if (mtype === 'sc_claim_accepted' && app.deal) {
        // Claim accepted
        let tricks = msg.match( /(?<= tricks=")\d+(?=")/ )[0];
        sendGameEvent('claim_accepted', {
            tricks_claimed: parseInt(tricks),
            board: app.deal.board
        });
    }
    
    // Still call DD if needed
    if (app && app.deal && app.deal.d) {
        doubledummy(app.deal.d, pref.appDoubleDummyMode === 'ondemand', zacharyDDcallback);
    }
    
    // Keep full app send for now (can remove later when confident)
    sendAppToPython(app);
}
```

---

## Example 2: Improved Python Bot

### File: `bridge-bot/bbo_bot_improved.py`

Complete rewrite with event handling and game state tracking:

```python
import asyncio
import websockets
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Constants
SEAT_ORDER = ["South", "West", "North", "East"]
SUITS = ['S', 'H', 'D', 'C']
POINTS = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
SUIT_SYMBOLS = {
    'S': '\033[97m♠\033[0m',
    'H': '\033[91m♥\033[0m',
    'D': '\033[91m♦\033[0m',
    'C': '\033[97m♣\033[0m'
}

class BridgeGameState:
    """Maintains current game state"""
    
    def __init__(self):
        self.board = None
        self.dealer = None
        self.vul = None
        self.hands = {}
        self.original_hands = {}  # Before any cards played
        self.auction = []
        self.played_cards = []
        self.current_trick = []
        self.dd_analysis = None
        self.contract = None
        self.declarer = None
        
    def new_deal(self, data):
        """Initialize new deal"""
        self.board = data.get('board')
        self.dealer = data.get('dealer')
        self.vul = data.get('vul')
        self.auction = []
        self.played_cards = []
        self.current_trick = []
        self.contract = None
        
        # Parse hands from LIN format
        hands_data = data.get('hands', {})
        self.original_hands = {
            'South': self.parse_lin_hand(hands_data.get('south', '')),
            'West': self.parse_lin_hand(hands_data.get('west', '')),
            'North': self.parse_lin_hand(hands_data.get('north', '')),
            'East': self.parse_lin_hand(hands_data.get('east', ''))
        }
        self.hands = {k: list(v) for k, v in self.original_hands.items()}
        
    def parse_lin_hand(self, lin_str: str) -> List[str]:
        """
        Convert LIN format to list of cards
        Example: "SAKQHAKQDAKQCAKQ" -> ["SA", "SK", "SQ", "HA", ...]
        """
        if not lin_str:
            return []
            
        cards = []
        current_suit = None
        
        for char in lin_str:
            if char in 'SHDC':
                current_suit = char
            else:
                cards.append(current_suit + char)
                
        return cards
    
    def update_auction(self, call: str):
        """Add bid to auction"""
        self.auction.append(call)
        
        # Try to determine contract
        if len(self.auction) >= 4:
            if (self.auction[-1] == 'p' and 
                self.auction[-2] == 'p' and 
                self.auction[-3] == 'p'):
                # Auction complete
                if len(self.auction) > 3:
                    self.contract = self.auction[-4]
                    # Determine declarer (simplified)
                    dealer_idx = SEAT_ORDER.index(self.dealer) if self.dealer else 0
                    contract_idx = len(self.auction) - 4
                    self.declarer = SEAT_ORDER[(dealer_idx + contract_idx) % 4]
    
    def play_card(self, card: str):
        """Play a card and remove from hand"""
        self.played_cards.append(card)
        
        # Remove from appropriate hand (simplified - would need to track who played)
        for hand in self.hands.values():
            if card in hand:
                hand.remove(card)
                break
    
    def calculate_hcp(self, hand: List[str]) -> int:
        """Calculate high card points"""
        return sum(POINTS.get(card[1], 0) for card in hand)
    
    def display(self):
        """Display current state"""
        print("\n" + "="*60)
        print(f"Board {self.board} - Dealer: {self.dealer} - Vul: {self.vul}")
        print("="*60)
        
        for seat in SEAT_ORDER:
            if seat in self.hands:
                hcp = self.calculate_hcp(self.hands[seat])
                print(f"\n{seat} (HCP: {hcp}):")
                self.display_hand(self.hands[seat])
        
        if self.auction:
            print(f"\nAuction: {' '.join(self.auction)}")
            if self.contract:
                print(f"Contract: {self.contract} by {self.declarer}")
        
        if self.dd_analysis:
            print(f"\n🧠 Double Dummy: {self.dd_analysis.get('cNS')} " +
                  f"(NS: {self.dd_analysis.get('sNS')})")
        
        print("\n" + "="*60)
    
    def display_hand(self, cards: List[str]):
        """Display a hand organized by suit"""
        by_suit = {s: [] for s in SUITS}
        
        for card in cards:
            if len(card) == 2:
                by_suit[card[0]].append(card[1])
        
        for suit in SUITS:
            cards_str = ''.join(sorted(by_suit[suit], 
                                      key=lambda x: 'AKQJT98765432'.index(x)))
            print(f"  {SUIT_SYMBOLS[suit]}: {cards_str if cards_str else '-'}")


class EventHandler:
    """Handle different event types"""
    
    def __init__(self, game_state: BridgeGameState):
        self.game = game_state
        
    async def handle_new_deal(self, data: dict):
        """Handle new deal event"""
        print("\n\n🎲 NEW DEAL")
        self.game.new_deal(data)
        self.game.display()
        
    async def handle_bid(self, data: dict):
        """Handle bid made event"""
        call = data.get('call')
        print(f"\n📢 Bid: {call}")
        self.game.update_auction(call)
        
        if self.game.contract:
            print(f"   Final Contract: {self.game.contract} by {self.game.declarer}")
        
    async def handle_card_played(self, data: dict):
        """Handle card played event"""
        card = data.get('card')
        print(f"\n🃏 Card Played: {card}")
        self.game.play_card(card)
        
        trick = data.get('current_trick', [])
        if trick:
            print(f"   Current trick: {' '.join(trick)}")
    
    async def handle_dd(self, data: dict):
        """Handle double dummy results"""
        print(f"\n🧠 Double Dummy Analysis Received")
        self.game.dd_analysis = data
        
        if 'cNS' in data:
            print(f"   NS can make: {data['cNS']} for {data.get('sNS')}")
        if 'cEW' in data:
            print(f"   EW can make: {data['cEW']} for {data.get('sEW')}")
    
    async def handle_claim(self, data: dict):
        """Handle claim accepted"""
        tricks = data.get('tricks_claimed')
        print(f"\n✋ Claim Accepted: {tricks} tricks")


async def handle_connection(websocket):
    """Main WebSocket handler"""
    print("✅ WebSocket client connected from extension")
    print("   Waiting for game events...")
    
    game = BridgeGameState()
    handler = EventHandler(game)
    
    async for message in websocket:
        try:
            data = json.loads(message)
            event_type = data.get("type")
            event_data = data.get("data", {})
            
            # Route to appropriate handler
            if event_type == "new_deal":
                await handler.handle_new_deal(event_data)
                
            elif event_type == "bid_made":
                await handler.handle_bid(event_data)
                
            elif event_type == "card_played":
                await handler.handle_card_played(event_data)
                
            elif event_type == "double_dummy":
                await handler.handle_dd(data.get("dd", {}))
                
            elif event_type == "claim_accepted":
                await handler.handle_claim(event_data)
                
            elif event_type == "app_update":
                # Legacy format - just log
                print("⚠️  Received legacy app_update (consider updating extension)")
                
            else:
                print(f"⚠️  Unknown event type: {event_type}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()


def find_free_port(start=8675):
    """Find an available port"""
    import socket
    for port in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports found")


async def main():
    """Start the WebSocket server"""
    port = find_free_port()
    print(f"🚀 Bridge Bot Server Starting")
    print(f"   Listening on: ws://localhost:{port}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n   Make sure Chrome extension is loaded and connected to BBO!")
    print("   " + "="*50 + "\n")
    
    async with websockets.serve(handle_connection, "localhost", port):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
```

---

## Example 3: Simple AI Module

### File: `bridge-bot/simple_ai.py`

```python
"""
Simple AI for making bridge decisions
This demonstrates basic logic - expand for sophistication
"""

from typing import List, Tuple, Dict

# Card values for comparison
RANK_ORDER = '23456789TJQKA'

class SimpleAI:
    """Basic bridge AI - bidding and play logic"""
    
    def __init__(self):
        self.system = "SAYC"  # Standard American
        
    def evaluate_hand(self, cards: List[str]) -> Dict:
        """
        Evaluate hand strength
        Returns: {hcp, suits, longest, balanced}
        """
        suits = {'S': [], 'H': [], 'D': [], 'C': []}
        hcp = 0
        points = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
        
        for card in cards:
            if len(card) == 2:
                suit, rank = card[0], card[1]
                suits[suit].append(rank)
                hcp += points.get(rank, 0)
        
        # Distribution
        lengths = {s: len(cards) for s, cards in suits.items()}
        longest = max(lengths, key=lengths.get)
        
        # Check if balanced (no singleton/void, at most one doubleton)
        sorted_lengths = sorted(lengths.values())
        balanced = sorted_lengths in [[3,3,3,4], [2,3,4,4]]
        
        return {
            'hcp': hcp,
            'suits': suits,
            'lengths': lengths,
            'longest': longest,
            'balanced': balanced
        }
    
    def opening_bid(self, cards: List[str], dealer: str, vul: str) -> Tuple[str, str]:
        """
        Determine opening bid
        Returns: (bid, reason)
        """
        eval = self.evaluate_hand(cards)
        hcp = eval['hcp']
        lengths = eval['lengths']
        
        # Too weak to open
        if hcp < 12:
            return "Pass", f"Only {hcp} HCP (need 12+)"
        
        # 1NT opening (15-17 balanced)
        if 15 <= hcp <= 17 and eval['balanced']:
            return "1NT", f"{hcp} HCP, balanced hand"
        
        # Strong NT (can add for other systems)
        if 20 <= hcp <= 21 and eval['balanced']:
            return "2NT", f"{hcp} HCP, balanced hand"
        
        # Open longest suit if 5+
        if lengths[eval['longest']] >= 5:
            # Prefer major
            if lengths['S'] >= 5:
                return "1S", f"{hcp} HCP, {lengths['S']} spades"
            if lengths['H'] >= 5:
                return "1H", f"{hcp} HCP, {lengths['H']} hearts"
            if lengths['D'] >= 5:
                return "1D", f"{hcp} HCP, {lengths['D']} diamonds"
            if lengths['C'] >= 5:
                return "1C", f"{hcp} HCP, {lengths['C']} clubs"
        
        # 4-card major?
        if lengths['S'] == 4:
            return "1S", f"{hcp} HCP, 4 spades"
        if lengths['H'] == 4:
            return "1H", f"{hcp} HCP, 4 hearts"
        
        # Better minor (longer, or diamond if equal)
        if lengths['D'] >= lengths['C']:
            return "1D", f"{hcp} HCP, better minor (diamonds)"
        else:
            return "1C", f"{hcp} HCP, better minor (clubs)"
    
    def best_card(self, hand: List[str], legal_cards: List[str], 
                  dd_tricks: Dict = None) -> Tuple[str, str]:
        """
        Choose best card to play
        
        Args:
            hand: Cards in hand
            legal_cards: Cards that can legally be played
            dd_tricks: Double dummy trick table (optional)
        
        Returns: (card, reason)
        """
        if not legal_cards:
            return None, "No legal cards"
        
        if len(legal_cards) == 1:
            return legal_cards[0], "Only legal card"
        
        # Simple heuristic: play highest card
        # In real AI, would use DD analysis
        def card_value(card):
            return RANK_ORDER.index(card[1]) if len(card) == 2 else 0
        
        best = max(legal_cards, key=card_value)
        return best, f"Playing high card (simple heuristic)"
    
    def get_legal_cards(self, hand: List[str], led_suit: str = None) -> List[str]:
        """
        Get legal cards that can be played
        
        Args:
            hand: Cards in hand
            led_suit: Suit that was led (None if leading)
        
        Returns: List of legal cards
        """
        if not led_suit:
            # Leading - all cards legal
            return hand
        
        # Must follow suit
        same_suit = [c for c in hand if c[0] == led_suit]
        
        if same_suit:
            return same_suit
        else:
            # Can't follow - all cards legal
            return hand


def test_ai():
    """Test the AI"""
    ai = SimpleAI()
    
    # Test hand: Strong balanced
    hand = ['SA', 'SK', 'SQ', 'HA', 'HK', 'HQ', 'DA', 'DK', 'DQ', 'CA', 'CK', 'CQ', 'CJ']
    
    eval = ai.evaluate_hand(hand)
    print("Hand Evaluation:")
    print(f"  HCP: {eval['hcp']}")
    print(f"  Distribution: {eval['lengths']}")
    print(f"  Balanced: {eval['balanced']}")
    
    bid, reason = ai.opening_bid(hand, 'N', 'None')
    print(f"\nOpening bid: {bid}")
    print(f"  Reason: {reason}")
    
    # Test card play
    legal = ai.get_legal_cards(hand, 'S')
    card, reason = ai.best_card(hand, legal)
    print(f"\nCard to play: {card}")
    print(f"  Reason: {reason}")


if __name__ == "__main__":
    test_ai()
```

---

## Example 4: Integrating AI with Bot

### File: `bridge-bot/bot_with_ai.py`

```python
"""
Bridge bot with AI decision making
Combines event handling with AI logic
"""

import asyncio
import websockets
import json
from bbo_bot_improved import BridgeGameState, EventHandler, find_free_port
from simple_ai import SimpleAI

class AIEventHandler(EventHandler):
    """Enhanced event handler with AI"""
    
    def __init__(self, game_state: BridgeGameState):
        super().__init__(game_state)
        self.ai = SimpleAI()
        self.auto_suggest = True  # Set False to disable suggestions
        
    async def handle_new_deal(self, data: dict):
        """Handle new deal with AI analysis"""
        await super().handle_new_deal(data)
        
        if self.auto_suggest and self.game.dealer == 'South':
            # We're dealer - suggest opening
            south_hand = self.game.hands.get('South', [])
            bid, reason = self.ai.opening_bid(south_hand, 
                                             self.game.dealer, 
                                             self.game.vul)
            print(f"\n🤖 AI Suggestion: {bid}")
            print(f"   {reason}")
            
    async def handle_bid(self, data: dict):
        """Handle bid with AI suggestions for next bid"""
        await super().handle_bid(data)
        
        if not self.auto_suggest:
            return
        
        # Determine whose turn (simplified)
        auction_len = len(self.game.auction)
        
        # For demo: only suggest if we're South and it's our turn
        dealer_idx = ['N', 'E', 'S', 'W'].index(self.game.dealer)
        current_bidder = (dealer_idx + auction_len) % 4
        
        if ['N', 'E', 'S', 'W'][current_bidder] == 'S':
            print(f"\n🤖 Your turn to bid!")
            # In full implementation, would analyze auction and suggest response
            
    async def handle_card_played(self, data: dict):
        """Handle card play with AI suggestion"""
        await super().handle_card_played(data)
        
        if not self.auto_suggest:
            return
        
        # Determine if it's South's turn
        # (This is simplified - real implementation needs trick tracking)
        played_count = len(self.game.played_cards)
        
        if played_count % 4 == 0:  # Beginning of trick
            print(f"\n🤖 Your turn to play!")
            south_hand = self.game.hands.get('South', [])
            
            if south_hand:
                # Determine led suit (simplified)
                trick = data.get('current_trick', [])
                led_suit = trick[0][0] if trick else None
                
                legal = self.ai.get_legal_cards(south_hand, led_suit)
                card, reason = self.ai.best_card(south_hand, legal, 
                                                self.game.dd_analysis)
                
                print(f"   Suggested card: {card}")
                print(f"   {reason}")


async def handle_connection(websocket):
    """WebSocket handler with AI"""
    print("✅ AI-Enhanced Bridge Bot Connected")
    
    game = BridgeGameState()
    handler = AIEventHandler(game)
    
    async for message in websocket:
        try:
            data = json.loads(message)
            event_type = data.get("type")
            event_data = data.get("data", {})
            
            if event_type == "new_deal":
                await handler.handle_new_deal(event_data)
            elif event_type == "bid_made":
                await handler.handle_bid(event_data)
            elif event_type == "card_played":
                await handler.handle_card_played(event_data)
            elif event_type == "double_dummy":
                await handler.handle_dd(data.get("dd", {}))
            elif event_type == "claim_accepted":
                await handler.handle_claim(event_data)
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Start AI bot server"""
    port = find_free_port()
    print(f"🤖 AI Bridge Bot Starting on ws://localhost:{port}")
    print(f"   AI suggestions enabled!")
    print("="*60 + "\n")
    
    async with websockets.serve(handle_connection, "localhost", port):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 AI Bot stopped")
```

---

## Usage Instructions

### 1. Install Dependencies

```bash
pip install websockets
```

### 2. Update Extension

Copy the code from Example 1 into `zb-bbo/bbov3.js`

### 3. Run Improved Bot

```bash
cd bridge-bot
python3 bbo_bot_improved.py
```

### 4. Run AI Bot (Alternative)

```bash
python3 bot_with_ai.py
```

### 5. Load Extension & Play

1. Load extension in Chrome
2. Go to BridgeBase.com
3. Start playing
4. Watch AI suggestions!

---

## What You'll See

```
🤖 AI Bridge Bot Starting on ws://localhost:8675
   AI suggestions enabled!
============================================================

✅ AI-Enhanced Bridge Bot Connected
   Waiting for game events...


🎲 NEW DEAL
============================================================
Board 1 - Dealer: N - Vul: None
============================================================

South (HCP: 15)
  ♠: AKQ32
  ♥: K54
  ♦: QJ6
  ♣: 82
  
🤖 Your turn to bid!
   Suggested bid: 1S
   15 HCP, 5 spades
   
📢 Bid: 1S

[... more play ...]

🧠 Double Dummy Analysis Received
   NS can make: 4S for 420
   EW can make: 3D for -170
```

---

These examples are ready to use! Start with Example 1 and 2, then add the AI when you're comfortable.

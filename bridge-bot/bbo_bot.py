import asyncio
import websockets
import json
import socket
import hashlib
import re
from dd_analyzer import DoubleDummyAnalyzer, recommend_play
from decision_engine import DecisionEngine

SEAT_ORDER = ["South", "West", "North", "East"]
SUITS = ['S', 'H', 'D', 'C']
POINTS = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}

# State tracking
last_deal_hash = None
last_dd_hash = None
last_dd_result = None
decision_engine = DecisionEngine()

BOTTOM_SEAT = "South"  # Change to "East", "West", or "North" to control which hand is at the bottom

# Parse dot-format hand into suit dictionary
def parse_dot_hand(dot_str):
    suits = dot_str.split(".")
    return {suit: list(suits[i]) if i < len(suits) else [] for i, suit in enumerate(SUITS)}

# Remove played cards from each hand
def remove_played_cards(hands_dict, played_cards):
    for card in played_cards:
        suit, rank = card[0], card[1]
        for hand in hands_dict.values():
            if rank in hand.get(suit, []):
                hand[suit].remove(rank)

# Count high card points
def calculate_hcp(hand_by_suit):
    return sum(POINTS.get(card, 0) for suit in SUITS for card in hand_by_suit[suit])

# ANSI escape codes for colors
SUIT_SYMBOLS = {
    'S': '\033[97m♠\033[0m',  # White
    'H': '\033[91m♥\033[0m',  # Red
    'D': '\033[91m♦\033[0m',  # Red
    'C': '\033[97m♣\033[0m'   # White
}



# ANSI-safe string length (used for padding)
def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

# ANSI-safe left-align
def pad_right(s, width):
    return s + ' ' * (width - visible_len(s))

def format_suit_line(suit, cards):
    symbol = SUIT_SYMBOLS.get(suit, suit)
    return f"{symbol}: {''.join(cards)}"

def print_hand_summary(hands_dict):
    if last_dd_result:
        print(f"\n📣 Double Dummy Result: {last_dd_result.get('cNS')} (Score: {last_dd_result.get('sNS')})\n")

    def format_hand(hand):
        return [format_suit_line(s, hand[s]) for s in SUITS]

    # Map seat order so BOTTOM_SEAT is at the bottom, and others rotate accordingly
    seat_idx = SEAT_ORDER.index(BOTTOM_SEAT)
    seats = SEAT_ORDER[seat_idx:] + SEAT_ORDER[:seat_idx]
    top_seat = seats[2]   # Opposite of bottom
    left_seat = seats[1]
    right_seat = seats[3]
    bottom_seat = seats[0]

    hands = {seat: hands_dict.get(seat, {s: [] for s in SUITS}) for seat in SEAT_ORDER}
    hcps = {seat: calculate_hcp(hands[seat]) for seat in SEAT_ORDER}

    # Top (opposite of bottom)
    print(f"{' ' * 20}{top_seat} (HCP: {hcps[top_seat]})")
    for line in format_hand(hands[top_seat]):
        print(f"{' ' * 14}{line}")
    print()

    # Middle (left and right)
    left_lines = format_hand(hands[left_seat])
    right_lines = format_hand(hands[right_seat])
    max_lines = max(len(left_lines), len(right_lines))
    print(f"{pad_right(left_seat + ' (HCP: ' + str(hcps[left_seat]) + ')', 26)}{' ' * 8}{right_seat} (HCP: {hcps[right_seat]})")
    for i in range(max_lines):
        l_line = left_lines[i] if i < len(left_lines) else ""
        r_line = right_lines[i] if i < len(right_lines) else ""
        print(f"{pad_right(l_line, 26)}{' ' * 8}{r_line}")
    print()

    # Bottom (selected seat)
    print(f"{' ' * 20}{bottom_seat} (HCP: {hcps[bottom_seat]})")
    for line in format_hand(hands[bottom_seat]):
        print(f"{' ' * 14}{line}")
    print()



# Handle app data
def analyze_app(app):
    global last_deal_hash

    deal_data = app.get("deal", {})
    if "d" not in deal_data or "hand" not in deal_data["d"]:
        return

    # Hash the deal to see if it's changed
    deal_hash = hashlib.md5(json.dumps(deal_data, sort_keys=True).encode()).hexdigest()
    if deal_hash == last_deal_hash:
        return
    last_deal_hash = deal_hash

    hands = deal_data["d"]["hand"]
    if len(hands) != 4:
        return

    played_cards = deal_data.get("play", [])
    hands_dict = {SEAT_ORDER[i]: parse_dot_hand(hands[i]) for i in range(4)}
    remove_played_cards(hands_dict, played_cards)
    print_hand_summary(hands_dict)

# Handle DD result updates
def handle_dd_result(data):
    global last_dd_hash, last_dd_result, decision_engine

    dd_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    if dd_hash == last_dd_hash:
        return

    last_dd_hash = dd_hash
    last_dd_result = data
    
    print("\n" + "="*60)
    print("🧠 DOUBLE DUMMY ANALYSIS RECEIVED")
    print("="*60)
    
    # Create analyzer and display formatted results
    analyzer = DoubleDummyAnalyzer(data)
    print(analyzer.format_analysis())
    print("="*60)
    
    # Update decision engine with DD data
    decision_engine.update_dd_analysis(data)
    
    # Trigger reprint of current hands with updated DD info
    if last_deal_hash:
        print_hand_summary(hands_dict_cache)

# WebSocket handler
hands_dict_cache = {}
current_board = None
current_auction = []
current_played_cards = []

def handle_game_event(event_type, event_data):
    """Handle event-based messages from Chrome extension"""
    global hands_dict_cache, current_board, current_auction, current_played_cards, decision_engine
    
    if event_type == "new_deal":
        # New deal started
        current_board = event_data.get("board")
        current_auction = []
        current_played_cards = []
        
        print(f"\n{'='*60}")
        print(f"🃏 NEW DEAL - Board {current_board}")
        print(f"   Dealer: {event_data.get('dealer')}, Vul: {event_data.get('vul')}")
        print(f"{'='*60}")
        
        # Parse hands
        hands = event_data.get("hands", {})
        hands_dict_cache = {}
        hands_lin = {}  # Keep LIN format for decision engine
        for seat in SEAT_ORDER:
            seat_key = seat.lower()
            if seat_key in hands:
                lin_hand = hands[seat_key]
                # Convert LIN format to dot format (simplified)
                # LIN: SAKQHAKQJAKQJAKQ -> Dot: AKQ.AKQ.AKQ.AKQ
                # This is a simplified conversion - may need adjustment
                hands_dict_cache[seat] = parse_lin_hand(lin_hand)
                # Map to decision engine format (N/S/E/W)
                de_seat = {'South': 'S', 'West': 'W', 'North': 'N', 'East': 'E'}[seat]
                hands_lin[de_seat] = lin_hand
        
        # Initialize decision engine with new deal
        decision_engine.reset_deal(
            current_board,
            event_data.get('dealer'),
            event_data.get('vul'),
            hands_lin
        )
        
        print_hand_summary(hands_dict_cache)
        
    elif event_type == "bid_made":
        # Bid was made
        call = event_data.get("call")
        bidder = event_data.get("bidder", "?")
        current_auction = event_data.get("auction", [])
        time = event_data.get("time", 0)
        print(f"📢 {bidder} bids: {call.upper()} (after {time:.2f}s)")
        
        # Update decision engine
        decision_engine.update_auction(call, bidder)
        
    elif event_type == "card_played":
        # Card was played
        card = event_data.get("card")
        player = event_data.get("player", "?")
        played_count = event_data.get("played_count", 0)
        current_played_cards.append(card)
        
        # Remove card from hands and reprint
        suit, rank = card[0], card[1]
        for hand in hands_dict_cache.values():
            if rank in hand.get(suit, []):
                hand[suit].remove(rank)
                break
        
        print(f"🎴 {player} plays: {SUIT_SYMBOLS.get(suit, suit)}{rank} ({played_count + 1} cards played)")
        
        # Update decision engine with the card that was played
        decision_engine.update_card_played(player, card)
        
        # Now get recommendation for the NEXT player who needs to play
        if decision_engine.lead_player:
            # Show current trick status
            if decision_engine.current_trick:
                trick_so_far = ' '.join([f"{t['player']}:{t['card']}" for t in decision_engine.current_trick])
                print(f"   Current trick: {trick_so_far}")
            
            recommended_card, reasoning = decision_engine.get_recommendation()
            if recommended_card:
                rec_suit = SUIT_SYMBOLS.get(recommended_card[0], recommended_card[0])
                print(f"💡 Recommendation for {decision_engine.lead_player}: {rec_suit}{recommended_card[1]} - {reasoning}")
            elif reasoning:
                print(f"💭 {decision_engine.lead_player}: {reasoning}")
        
        print_hand_summary(hands_dict_cache)
        
    elif event_type == "claim_accepted":
        # Claim was accepted
        tricks = event_data.get("tricks_claimed")
        print(f"\n✅ Claim accepted: {tricks} tricks")
        print(f"{'='*60}\n")

def parse_lin_hand(lin_str):
    """Convert LIN format (SAKQHAKQ...) to suit dictionary"""
    hand = {s: [] for s in SUITS}
    current_suit = None
    for char in lin_str:
        if char in SUITS:
            current_suit = char
        elif current_suit:
            hand[current_suit].append(char)
    return hand

async def handle_connection(websocket):
    print("✅ WebSocket client connected.")
    async for message in websocket:
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # New event-based messages
            if msg_type == "game_event":
                event_type = data.get("event_type")
                event_data = data.get("data", {})
                print(f"🎯 Received event: {event_type}")  # DEBUG
                handle_game_event(event_type, event_data)
            
            # DD result message
            elif msg_type == "dd_result":
                print(f"🎯 Received DD result for board {data.get('board')}")  # DEBUG
                handle_dd_result(data)
            
            # Legacy messages (keep for backward compatibility)
            elif msg_type == "app_update":
                app = data.get("app")
                analyze_app(app)
            elif msg_type == "double_dummy":
                handle_dd_result(data.get("dd"))
        except Exception as e:
            print("❌ Error:", e)
            import traceback
            traceback.print_exc()

# Find free port to avoid collisions
def find_free_port(start=8675):
    for port in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports found.")

# Entry point
async def main():
    port = find_free_port()
    print(f"🚀 Server running at ws://localhost:{port}")
    async with websockets.serve(handle_connection, "localhost", port):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

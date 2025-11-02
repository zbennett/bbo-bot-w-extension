"""
Web Dashboard for Bridge Bot
Real-time visualization of bridge games with DDS analysis
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'bridge-bot-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state to track the current game
current_game_state = {
    'board_number': None,
    'dealer': None,
    'vulnerability': None,
    'hands': {'N': [], 'E': [], 'S': [], 'W': []},
    'contract': None,
    'declarer': None,
    'current_trick': [],
    'tricks_won': {'NS': 0, 'EW': 0},
    'all_tricks': [],
    'last_recommendation': None,
    'bidding': [],
    'dd_analysis': None,
    'active_player': None,
    'bottom_seat': 'S',
    'last_trick_winner': None,
    'rubber_score': None  # Rubber bridge scoring
}

@app.route('/')
def index():
    """Serve the main dashboard page"""
    from flask import send_from_directory
    return send_from_directory('templates', 'dashboard_react.html')

@app.route('/modular')
def modular():
    """Serve the modular dashboard page (experimental)"""
    from flask import send_from_directory
    return send_from_directory('templates', 'dashboard_modular.html')

@app.route('/classic')
def classic():
    """Serve the classic dashboard page"""
    return render_template('dashboard.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('🌐 Dashboard client connected')
    # Send current game state to newly connected client
    emit('game_state', current_game_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('🌐 Dashboard client disconnected')

def broadcast_game_state():
    """Broadcast the current game state to all connected clients"""
    socketio.emit('game_state', current_game_state)

def broadcast_event(event_type, data):
    """Broadcast a specific event to all connected clients"""
    socketio.emit('game_event', {'type': event_type, 'data': data})

# Public API for the bot to update the dashboard
class DashboardBroadcaster:
    """Interface for the bot to send updates to the dashboard"""
    
    @staticmethod
    def update_new_deal(board_number, dealer, vulnerability, hands):
        """Update dashboard with new deal information"""
        current_game_state['board_number'] = board_number
        current_game_state['dealer'] = dealer
        current_game_state['vulnerability'] = vulnerability
        # Store hands as-is (dashboard will use list copies for display)
        current_game_state['hands'] = hands
        current_game_state['contract'] = None
        current_game_state['declarer'] = None
        current_game_state['current_trick'] = []
        current_game_state['tricks_won'] = {'NS': 0, 'EW': 0}
        current_game_state['all_tricks'] = []
        current_game_state['bidding'] = []
        current_game_state['dd_analysis'] = None
        current_game_state['last_recommendation'] = None
        current_game_state['last_trick_winner'] = None
        
        broadcast_game_state()
        broadcast_event('new_deal', {
            'board_number': board_number,
            'dealer': dealer,
            'vulnerability': vulnerability
        })
    
    @staticmethod
    def update_bid(player, bid, timing):
        """Update dashboard with new bid"""
        bid_info = {'player': player, 'bid': bid, 'timing': timing}
        current_game_state['bidding'].append(bid_info)
        broadcast_event('bid_made', bid_info)
        broadcast_game_state()  # Send full state so UI updates immediately
    
    @staticmethod
    def update_contract(contract, declarer):
        """Update dashboard with final contract"""
        current_game_state['contract'] = contract
        current_game_state['declarer'] = declarer
        broadcast_event('contract_set', {'contract': contract, 'declarer': declarer})
        broadcast_game_state()
    
    @staticmethod
    def update_card_played(player, card, trick_complete=False, winner=None):
        """Update dashboard with card played"""
        
        print(f"🎴 Dashboard update_card_played: player={player}, card={card}, trick_complete={trick_complete}, winner={winner}")
        print(f"   Current trick before: {current_game_state['current_trick']}")
        print(f"   Last trick winner: {current_game_state.get('last_trick_winner')}")
        
        # If there's a completed trick from last time, archive it now before adding new card
        if current_game_state.get('last_trick_winner'):
            print(f"   📦 Archiving previous trick with winner {current_game_state['last_trick_winner']}")
            # Move previous completed trick to history
            if current_game_state['current_trick']:
                current_game_state['all_tricks'].append({
                    'cards': current_game_state['current_trick'].copy(),
                    'winner': current_game_state['last_trick_winner']
                })
            current_game_state['current_trick'] = []
            current_game_state['last_trick_winner'] = None
        
        card_info = {'player': player, 'card': card}
        
        # Remove card from player's hand  
        if player in current_game_state['hands']:
            hand = current_game_state['hands'][player]
            card_found = False
            for i, c in enumerate(hand):
                if c == card:
                    hand.pop(i)
                    card_found = True
                    print(f"🎴 Dashboard: Removed {card} from {player}'s hand (had {len(hand)+1} cards, now {len(hand)})")
                    break
            if not card_found:
                print(f"⚠️  Dashboard: Card {card} not found in {player}'s hand: {hand}")
        else:
            print(f"⚠️  Dashboard: Player {player} not found in hands!")
        
        # Add the card to current trick
        current_game_state['current_trick'].append(card_info)
        
        if trick_complete and winner:
            # Mark trick as complete but DON'T clear it yet - keep it visible
            current_game_state['last_trick_winner'] = winner
            
            # Update trick count
            if winner in ['N', 'S']:
                current_game_state['tricks_won']['NS'] += 1
            else:
                current_game_state['tricks_won']['EW'] += 1
        
        broadcast_event('card_played', {
            'player': player,
            'card': card,
            'trick_complete': trick_complete,
            'winner': winner
        })
        broadcast_game_state()
    
    @staticmethod
    def update_recommendation(player, card, reasoning):
        """Update dashboard with DDS recommendation"""
        rec_info = {
            'player': player,
            'card': card,
            'reasoning': reasoning
        }
        current_game_state['last_recommendation'] = rec_info
        broadcast_event('recommendation', rec_info)
        broadcast_game_state()
    
    @staticmethod
    def update_dd_analysis(analysis_data):
        """Update dashboard with full DD analysis"""
        current_game_state['dd_analysis'] = analysis_data
        broadcast_event('dd_analysis', analysis_data)
        broadcast_game_state()
    
    @staticmethod
    def update_active_player(player):
        """Update which player's turn it is"""
        current_game_state['active_player'] = player
        broadcast_game_state()
    
    @staticmethod
    def set_bottom_seat(seat):
        """Set which seat appears at bottom of display"""
        current_game_state['bottom_seat'] = seat
        broadcast_game_state()
    
    @staticmethod
    def update_rubber_score(rubber_score):
        """Update dashboard with rubber scoring information"""
        print(f"📊 Web Dashboard: Updating rubber score: rubber_number={rubber_score.get('rubber_number')}, hand_count={rubber_score.get('hand_count')}")
        current_game_state['rubber_score'] = rubber_score
        socketio.emit('rubber_score', rubber_score)
        broadcast_game_state()

def start_dashboard(port=5000):
    """Start the dashboard server in a separate thread"""
    def run_server():
        print(f'🌐 Starting web dashboard on http://localhost:{port}')
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    
    dashboard_thread = threading.Thread(target=run_server, daemon=True)
    dashboard_thread.start()
    return dashboard_thread

if __name__ == '__main__':
    # Run standalone for testing
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

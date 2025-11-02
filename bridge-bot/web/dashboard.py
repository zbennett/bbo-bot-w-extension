"""
Web Dashboard for Bridge Bot - Refactored
Modular architecture with separated concerns
"""

from flask import Flask, send_from_directory, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

from .state import GameState
from .broadcaster import DashboardBroadcaster

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates')
app.config['SECRET_KEY'] = 'bridge-bot-secret'
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize game state
game_state = GameState()

# Initialize broadcaster
broadcaster = DashboardBroadcaster(socketio, game_state)


# ==================== Routes ====================

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('../templates', 'dashboard_react.html')


@app.route('/modular')
def modular():
    """Serve the modular dashboard page"""
    return send_from_directory('../templates', 'dashboard_modular.html')


@app.route('/classic')
def classic():
    """Serve the classic dashboard page"""
    return render_template('dashboard.html')


# ==================== Socket.IO Handlers ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('🌐 Dashboard client connected')
    # Send current game state to newly connected client
    broadcaster.broadcast_game_state()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('👋 Dashboard client disconnected')


# ==================== Public API for Bot ====================

def update_new_deal(board_number, dealer, vulnerability, hands, bottom_seat='S'):
    """
    Update dashboard with a new deal
    
    Args:
        board_number: Board number
        dealer: Dealer position (N/E/S/W)
        vulnerability: Vulnerability string
        hands: Dict of hands {player: [cards]}
        bottom_seat: Seat at bottom of display (default 'S')
    """
    broadcaster.broadcast_new_deal(board_number, dealer, vulnerability, hands, bottom_seat)


def update_card_played(player, card, trick_complete=False, winner=None):
    """
    Update dashboard when a card is played
    
    Args:
        player: Player who played the card
        card: Card that was played
        trick_complete: Whether the trick is complete
        winner: Winner of the trick (if complete)
    """
    broadcaster.broadcast_card_played(player, card, trick_complete, winner)


def update_bid(player, bid):
    """
    Update dashboard with a new bid
    
    Args:
        player: Player who made the bid
        bid: Bid that was made
    """
    broadcaster.broadcast_bid(player, bid)


def update_contract(contract, declarer):
    """
    Update dashboard with the final contract
    
    Args:
        contract: Contract string (e.g., "3NT")
        declarer: Declarer position
    """
    broadcaster.broadcast_contract(contract, declarer)


def update_recommendation(player, card, reason=None):
    """
    Update dashboard with a recommendation
    
    Args:
        player: Player to play
        card: Recommended card
        reason: Optional reason for the recommendation
    """
    broadcaster.broadcast_recommendation(player, card, reason)


def update_dd_analysis(analysis):
    """
    Update dashboard with double dummy analysis
    
    Args:
        analysis: DD analysis data
    """
    broadcaster.broadcast_dd_analysis(analysis)


def update_active_player(player):
    """
    Update dashboard with the active player
    
    Args:
        player: Active player position
    """
    broadcaster.broadcast_active_player(player)


def start_server(host='0.0.0.0', port=5001, debug=False):
    """
    Start the dashboard server
    
    Args:
        host: Host address (default: all interfaces)
        port: Port number (default: 5001)
        debug: Debug mode (default: False)
    """
    print(f"🌐 Starting web dashboard on http://localhost:{port}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

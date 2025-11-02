"""
Socket.IO Event Broadcaster
Handles all Socket.IO event emissions to connected clients
"""

from flask_socketio import emit

class DashboardBroadcaster:
    """Broadcasts game events to all connected dashboard clients"""
    
    def __init__(self, socketio, game_state):
        self.socketio = socketio
        self.game_state = game_state
    
    def broadcast_game_state(self):
        """Broadcast the complete game state"""
        self.socketio.emit('game_state', self.game_state.get_state())
    
    def broadcast_new_deal(self, board_number, dealer, vulnerability, hands, bottom_seat='S'):
        """Broadcast a new deal"""
        self.game_state.set_new_deal(board_number, dealer, vulnerability, hands, bottom_seat)
        
        self.socketio.emit('new_deal', {
            'board_number': board_number,
            'dealer': dealer,
            'vulnerability': vulnerability,
            'hands': hands,
            'bottom_seat': bottom_seat
        })
        
        print(f"📤 Broadcasted new deal: Board {board_number}")
    
    def broadcast_card_played(self, player, card, trick_complete=False, winner=None):
        """Broadcast a card play"""
        # Handle delayed trick clearing
        if self.game_state.get('last_trick_winner'):
            # Archive previous trick before adding new card
            pass  # Already handled in complete_trick
        
        # Remove card from player's hand
        if self.game_state.remove_card_from_hand(player, card):
            print(f"🎴 Removed {card} from {player}'s hand")
        else:
            print(f"⚠️  Could not remove {card} from {player}'s hand")
        
        # Add card to current trick
        self.game_state.add_card_to_trick(player, card)
        
        # Complete trick if applicable
        if trick_complete and winner:
            self.game_state.complete_trick(winner)
        
        self.socketio.emit('card_played', {
            'player': player,
            'card': card,
            'hands': self.game_state.get('hands'),
            'current_trick': self.game_state.get('current_trick'),
            'all_tricks': self.game_state.get('all_tricks'),
            'winner': winner if trick_complete else None
        })
    
    def broadcast_bid(self, player, bid):
        """Broadcast a bid"""
        bid_info = {'player': player, 'bid': bid}
        self.game_state.add_bid(bid_info)
        
        self.socketio.emit('bid_made', bid_info)
    
    def broadcast_contract(self, contract, declarer):
        """Broadcast the final contract"""
        self.game_state.set_contract(contract, declarer)
        
        self.socketio.emit('contract_set', {
            'contract': contract,
            'declarer': declarer
        })
        
        print(f"📤 Broadcasted contract: {contract} by {declarer}")
    
    def broadcast_recommendation(self, player, card, reason=None):
        """Broadcast a recommendation"""
        self.game_state.set_recommendation(player, card, reason)
        
        self.socketio.emit('recommendation', {
            'player': player,
            'card': card,
            'reason': reason
        })
    
    def broadcast_dd_analysis(self, analysis):
        """Broadcast double dummy analysis"""
        self.game_state.set_dd_analysis(analysis)
        
        self.socketio.emit('dd_analysis', {
            'analysis': analysis
        })
        
        print(f"📤 Broadcasted DD analysis")
    
    def broadcast_active_player(self, player):
        """Broadcast the active player"""
        self.game_state.set_active_player(player)
        
        self.socketio.emit('active_player', {
            'player': player
        })
    
    def broadcast_rubber_score(self, rubber_score):
        """Broadcast rubber scoring update"""
        self.game_state.set_rubber_score(rubber_score)
        
        self.socketio.emit('rubber_score', rubber_score)
        
        print(f"📤 Broadcasted rubber score update")

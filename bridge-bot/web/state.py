"""
Game State Management
Centralized game state with helper methods
"""

class GameState:
    """Manages the current bridge game state"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset to initial state"""
        self._state = {
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
            'last_trick_winner': None
        }
    
    def get_state(self):
        """Get the current state as a dictionary"""
        return self._state.copy()
    
    def update(self, **kwargs):
        """Update multiple state fields"""
        for key, value in kwargs.items():
            if key in self._state:
                self._state[key] = value
            else:
                raise KeyError(f"Unknown state field: {key}")
    
    def get(self, key, default=None):
        """Get a single state field"""
        return self._state.get(key, default)
    
    def set(self, key, value):
        """Set a single state field"""
        if key in self._state:
            self._state[key] = value
        else:
            raise KeyError(f"Unknown state field: {key}")
    
    # Convenience methods for common operations
    
    def set_new_deal(self, board_number, dealer, vulnerability, hands, bottom_seat='S'):
        """Set up a new deal"""
        self._state.update({
            'board_number': board_number,
            'dealer': dealer,
            'vulnerability': vulnerability,
            'hands': hands,
            'bottom_seat': bottom_seat,
            'current_trick': [],
            'all_tricks': [],
            'contract': None,
            'declarer': None,
            'last_trick_winner': None,
            'tricks_won': {'NS': 0, 'EW': 0},
            'bidding': []
        })
    
    def add_bid(self, bid_info):
        """Add a bid to the bidding sequence"""
        self._state['bidding'].append(bid_info)
    
    def set_contract(self, contract, declarer):
        """Set the final contract"""
        self._state['contract'] = contract
        self._state['declarer'] = declarer
    
    def add_card_to_trick(self, player, card):
        """Add a card to the current trick"""
        self._state['current_trick'].append({
            'player': player,
            'card': card
        })
    
    def complete_trick(self, winner):
        """Complete the current trick"""
        # Archive the trick
        self._state['all_tricks'].append({
            'cards': self._state['current_trick'].copy(),
            'winner': winner
        })
        
        # Update tricks won
        if winner in ['N', 'S']:
            self._state['tricks_won']['NS'] += 1
        else:
            self._state['tricks_won']['EW'] += 1
        
        # Clear current trick
        self._state['current_trick'] = []
        self._state['last_trick_winner'] = winner
    
    def remove_card_from_hand(self, player, card):
        """Remove a card from a player's hand"""
        if player in self._state['hands']:
            hand = self._state['hands'][player]
            if card in hand:
                hand.remove(card)
                return True
        return False
    
    def set_active_player(self, player):
        """Set the active (current) player"""
        self._state['active_player'] = player
    
    def set_recommendation(self, player, card, reason=None):
        """Set the current recommendation"""
        self._state['last_recommendation'] = {
            'player': player,
            'card': card,
            'reason': reason
        }
    
    def set_dd_analysis(self, analysis):
        """Set the double dummy analysis"""
        self._state['dd_analysis'] = analysis

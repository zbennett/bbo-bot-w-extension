"""
Decision Engine for Bridge Bot
Uses double dummy analysis to recommend optimal card plays.
"""

from dd_analyzer import DoubleDummyAnalyzer, recommend_play as dd_recommend_play

class DecisionEngine:
    """
    Main decision engine that tracks game state and makes play recommendations.
    """
    
    def __init__(self):
        self.board_number = None
        self.dealer = None
        self.vulnerability = None
        self.hands = {}  # {N: 'SAKQHAKQ...', S: ..., E: ..., W: ...}
        self.auction = []
        self.contract = None
        self.declarer = None
        self.dummy = None
        self.played_cards = []  # List of (player, card) tuples
        self.current_trick = []  # Current trick cards
        self.tricks_won = {'NS': 0, 'EW': 0}
        self.lead_player = None  # Who plays next
        self.dd_data = None
        
    def reset_deal(self, board, dealer, vul, hands):
        """Reset state for a new deal."""
        self.board_number = board
        self.dealer = dealer
        self.vulnerability = vul
        self.hands = hands.copy()
        self.auction = []
        self.contract = None
        self.declarer = None
        self.dummy = None
        self.played_cards = []
        self.current_trick = []
        self.tricks_won = {'NS': 0, 'EW': 0}
        self.lead_player = None
        self.dd_data = None
        
    def update_auction(self, call, bidder):
        """Update auction state with a new call."""
        self.auction.append({'call': call, 'bidder': bidder})
        
        # Determine contract and declarer if auction is complete
        if call.upper() in ['P', 'PASS'] and len(self.auction) >= 4:
            # Check if last 3 calls were all passes
            last_three = [a['call'].upper() for a in self.auction[-3:]]
            if all(c in ['P', 'PASS'] for c in last_three):
                self._finalize_contract()
                
    def _finalize_contract(self):
        """Determine the final contract and declarer from the auction."""
        # Find the last non-pass bid
        for i in range(len(self.auction) - 1, -1, -1):
            call = self.auction[i]['call'].upper()
            if call not in ['P', 'PASS', 'X', 'XX']:
                self.contract = call
                self.declarer = self.auction[i]['bidder']
                # Dummy is partner of declarer
                declarer_idx = ['N', 'E', 'S', 'W'].index(self.declarer)
                dummy_idx = (declarer_idx + 2) % 4
                self.dummy = ['N', 'E', 'S', 'W'][dummy_idx]
                
                # Lead player is LHO of declarer
                self.lead_player = ['N', 'E', 'S', 'W'][(declarer_idx + 1) % 4]
                break
                
    def update_card_played(self, player, card):
        """Update state with a played card."""
        # Validate player
        if player not in ['N', 'E', 'S', 'W']:
            # Invalid player (e.g., '?'), skip update
            return
            
        self.played_cards.append((player, card))
        self.current_trick.append({'player': player, 'card': card})
        
        # If trick is complete (4 cards), determine winner and reset
        if len(self.current_trick) == 4:
            winner = self._determine_trick_winner()
            if winner in ['N', 'S']:
                self.tricks_won['NS'] += 1
            else:
                self.tricks_won['EW'] += 1
            self.lead_player = winner
            self.current_trick = []
        else:
            # Next player is LHO of current player
            player_idx = ['N', 'E', 'S', 'W'].index(player)
            self.lead_player = ['N', 'E', 'S', 'W'][(player_idx + 1) % 4]
            
    def _determine_trick_winner(self):
        """Determine who won the current trick."""
        if not self.current_trick or not self.contract:
            return self.lead_player
            
        # Get trump suit from contract (last char)
        trump = self.contract[-1].upper()
        trump_map = {'C': 'clubs', 'D': 'diamonds', 'H': 'hearts', 'S': 'spades', 'N': None}
        trump_suit = trump_map.get(trump)
        
        # Get lead suit
        lead_card = self.current_trick[0]['card']
        lead_suit = self._get_suit(lead_card)
        
        # Find highest card that follows rules
        winner = self.current_trick[0]['player']
        highest_value = self._card_value(lead_card)
        highest_is_trump = (trump_suit and self._get_suit(lead_card) == trump_suit)
        
        for trick_card in self.current_trick[1:]:
            card = trick_card['card']
            card_suit = self._get_suit(card)
            card_value = self._card_value(card)
            card_is_trump = (trump_suit and card_suit == trump_suit)
            
            # Trump beats non-trump
            if card_is_trump and not highest_is_trump:
                winner = trick_card['player']
                highest_value = card_value
                highest_is_trump = True
            # Higher card in same suit wins
            elif card_is_trump == highest_is_trump:
                if card_suit == (trump_suit if highest_is_trump else lead_suit):
                    if card_value > highest_value:
                        winner = trick_card['player']
                        highest_value = card_value
                        
        return winner
        
    def _get_suit(self, card):
        """Extract suit from card (e.g., 'SA' -> 'spades')."""
        suit_char = card[0].upper()
        suit_map = {'S': 'spades', 'H': 'hearts', 'D': 'diamonds', 'C': 'clubs'}
        return suit_map.get(suit_char, 'unknown')
        
    def _card_value(self, card):
        """Get numeric value of card for comparison."""
        rank = card[1].upper()
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                  '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return values.get(rank, 0)
        
    def update_dd_analysis(self, dd_data):
        """Store double dummy analysis results."""
        self.dd_data = dd_data
        
    def get_recommendation(self):
        """
        Get a play recommendation for the current player.
        Returns: (recommended_card, reasoning) or (None, reason_string)
        """
        if not self.lead_player:
            return None, "No active player (waiting for auction to complete)"
            
        if not self.dd_data:
            return None, "No double dummy analysis available"
            
        # Get remaining cards for current player
        remaining_cards = self._get_remaining_cards(self.lead_player)
        if not remaining_cards:
            return None, f"{self.lead_player} has no cards remaining"
            
        # Extract trump suit from contract
        trump_suit = None
        if self.contract:
            # Contract format like "4H", "3NT", "2S", etc.
            if 'NT' in self.contract or 'N' in self.contract:
                trump_suit = 'NT'
            else:
                for suit in ['S', 'H', 'D', 'C']:
                    if suit in self.contract:
                        trump_suit = suit
                        break
            
        # Use DD analyzer to recommend best play
        try:
            analyzer = DoubleDummyAnalyzer(self.dd_data)
            card, reasoning = analyzer.analyze_position(
                self.lead_player, 
                remaining_cards,
                current_trick=self.current_trick,
                trump_suit=trump_suit
            )
            
            # Validate recommended card is actually in hand
            if card and card not in remaining_cards:
                print(f"⚠️  WARNING: Recommended {card} not in {self.lead_player}'s hand: {remaining_cards}")
                print(f"    Current trick: {self.current_trick}")
                print(f"    Trump: {trump_suit}")
                # Fallback: just play first available card
                card = remaining_cards[0]
                reasoning = f"Playing {card} (fallback due to logic error)"
            
            return card, reasoning
        except Exception as e:
            return None, f"Error analyzing position: {str(e)}"
            
    def _get_remaining_cards(self, player):
        """Get list of cards still in player's hand."""
        if player not in self.hands:
            return []
            
        # Convert LIN format to list of cards
        hand_lin = self.hands[player]
        cards = []
        
        suits = ['S', 'H', 'D', 'C']
        suit_idx = 0
        
        for char in hand_lin:
            if char.upper() in suits:
                suit_idx = suits.index(char.upper())
            elif char in 'AKQJT98765432':
                cards.append(suits[suit_idx] + char)
                
        # Remove played cards
        for played_player, played_card in self.played_cards:
            if played_player == player and played_card in cards:
                cards.remove(played_card)
                
        return cards
        
    def get_status_summary(self):
        """Get a summary of the current game state."""
        status = []
        status.append(f"Board #{self.board_number} | Dealer: {self.dealer} | Vul: {self.vulnerability}")
        
        if self.contract:
            status.append(f"Contract: {self.contract} by {self.declarer} | Dummy: {self.dummy}")
            status.append(f"Tricks: NS={self.tricks_won['NS']} EW={self.tricks_won['EW']}")
        else:
            status.append(f"Auction in progress ({len(self.auction)} calls)")
            
        if self.lead_player:
            remaining = self._get_remaining_cards(self.lead_player)
            status.append(f"To play: {self.lead_player} ({len(remaining)} cards left)")
            
        if self.current_trick:
            trick_str = " ".join([f"{c['player']}:{c['card']}" for c in self.current_trick])
            status.append(f"Current trick: {trick_str}")
            
        return "\n".join(status)

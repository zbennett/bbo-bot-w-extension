"""
Double Dummy Analyzer
Analyzes double dummy results to recommend optimal card play
"""

class DoubleDummyAnalyzer:
    """
    Analyzes double dummy results from BSOL server to determine best card to play
    
    DD Results Format (from BSOL):
    {
        'cNS': 'N 10 7D 10 10 9 8 8 6D',  # Contract string
        'sNS': '-420',                      # Score for NS
        'tricks': {
            'N': {'S': 10, 'H': 7, 'D': 10, 'C': 10},  # Tricks North can take from each suit lead
            'S': {'S': 9, 'H': 8, 'D': 8, 'C': 6},
            'E': {...},
            'W': {...}
        }
    }
    """
    
    def __init__(self, dd_data):
        self.dd = dd_data
        self.tricks = dd_data.get('tricks', {})
        self.contract = dd_data.get('cNS', '')
        self.score = dd_data.get('sNS', 0)
        
    def get_best_lead(self, player):
        """
        Get the best opening lead for a player
        
        Args:
            player: 'N', 'S', 'E', or 'W'
            
        Returns:
            Best suit to lead (  'S', 'H', 'D', or 'C')
        """
        if player not in self.tricks:
            return None
            
        player_tricks = self.tricks[player]
        
        # For defenders, want suit that gives them MOST tricks
        # For declarer/dummy, want suit that gives opponents LEAST tricks
        best_suit = max(player_tricks.keys(), key=lambda suit: player_tricks[suit])
        return best_suit
        
    def get_tricks_for_lead(self, player, suit):
        """
        Get number of tricks for a specific lead
        
        Args:
            player: 'N', 'S', 'E', or 'W'
            suit: 'S', 'H', 'D', or 'C'
            
        Returns:
            Number of tricks (integer)
        """
        if player not in self.tricks or suit not in self.tricks[player]:
            return 0
        return self.tricks[player][suit]
        
    def analyze_position(self, player, cards_in_hand):
        """
        Analyze current position and recommend best card to play
        
        Args:
            player: 'N', 'S', 'E', or 'W'
            cards_in_hand: List of cards like ['SA', 'HK', 'D7', 'C3']
            
        Returns:
            Recommended card to play with reasoning
        """
        if not cards_in_hand:
            return None, "No cards in hand"
            
        # Group cards by suit
        suits_in_hand = {}
        for card in cards_in_hand:
            suit = card[0]
            if suit not in suits_in_hand:
                suits_in_hand[suit] = []
            suits_in_hand[suit].append(card)
            
        # Get best suit based on DD analysis
        best_suit = self.get_best_lead(player)
        
        if best_suit and best_suit in suits_in_hand:
            # Play from best suit
            # For now, play highest card (TODO: more sophisticated logic)
            cards = suits_in_hand[best_suit]
            best_card = max(cards, key=lambda c: self._card_rank(c[1]))
            tricks = self.get_tricks_for_lead(player, best_suit)
            reason = f"DD analysis suggests {best_suit} (can make {tricks} tricks)"
            return best_card, reason
        else:
            # Fallback: play highest card from longest suit
            longest_suit = max(suits_in_hand.keys(), key=lambda s: len(suits_in_hand[s]))
            cards = suits_in_hand[longest_suit]
            best_card = max(cards, key=lambda c: self._card_rank(c[1]))
            return best_card, f"Playing high from longest suit ({longest_suit})"
            
    def _card_rank(self, rank):
        """Convert card rank to numeric value for comparison"""
        rank_order = '23456789TJQKA'
        return rank_order.index(rank) if rank in rank_order else 0
        
    def format_analysis(self):
        """Format DD results for display"""
        if not self.tricks:
            return "No double dummy data available"
            
        lines = []
        lines.append(f"📊 Double Dummy Analysis:")
        lines.append(f"   Contract: {self.contract}")
        lines.append(f"   Score (NS): {self.score}")
        lines.append(f"\n   Tricks by Lead:")
        
        for player in ['N', 'E', 'S', 'W']:
            if player in self.tricks:
                player_tricks = self.tricks[player]
                suits_str = '  '.join([f"{suit}:{player_tricks[suit]}" for suit in ['S', 'H', 'D', 'C'] if suit in player_tricks])
                lines.append(f"   {player}: {suits_str}")
                
        return '\n'.join(lines)


def recommend_play(dd_data, player, cards_in_hand):
    """
    Convenience function to get play recommendation
    
    Args:
        dd_data: Double dummy data dictionary
        player: 'N', 'S', 'E', or 'W'
        cards_in_hand: List of cards
        
    Returns:
        Tuple of (recommended_card, reasoning)
    """
    analyzer = DoubleDummyAnalyzer(dd_data)
    return analyzer.analyze_position(player, cards_in_hand)

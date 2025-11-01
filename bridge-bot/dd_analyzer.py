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
        
    def analyze_position(self, player, cards_in_hand, current_trick=None, trump_suit=None):
        """
        Analyze current position and recommend best card to play
        
        Args:
            player: 'N', 'S', 'E', or 'W'
            cards_in_hand: List of cards like ['SA', 'HK', 'D7', 'C3']
            current_trick: List of dicts [{'player': 'W', 'card': 'SA'}, ...] (cards played so far this trick)
            trump_suit: Trump suit ('S', 'H', 'D', 'C', or 'NT')
            
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
            
        # If we're following to a trick (not leading), must follow suit
        if current_trick and len(current_trick) > 0:
            led_suit = current_trick[0]['card'][0]  # First card's suit
            
            if led_suit in suits_in_hand:
                # Must follow suit - choose best card in that suit
                cards = suits_in_hand[led_suit]
                
                # Determine if we should try to win or play low
                # For now: play high if we can win, low otherwise
                high_card = max(cards, key=lambda c: self._card_rank(c[1]))
                low_card = min(cards, key=lambda c: self._card_rank(c[1]))
                
                # Simple heuristic: if partner is winning, play low; otherwise try to win
                highest_so_far = self._get_highest_card_in_trick(current_trick, led_suit, trump_suit)
                
                if self._can_beat(high_card, highest_so_far, led_suit, trump_suit):
                    return high_card, f"Following suit with high {led_suit} to try to win"
                else:
                    return low_card, f"Following suit with low {led_suit} (can't win)"
            else:
                # Can't follow - need to discard or trump
                trump = trump_suit if trump_suit != 'NT' else None
                
                if trump and trump in suits_in_hand:
                    # Can trump
                    cards = suits_in_hand[trump]
                    # Trump with lowest trump
                    trump_card = min(cards, key=lambda c: self._card_rank(c[1]))
                    return trump_card, f"Trumping with {trump_card}"
                else:
                    # Must discard - throw lowest card from longest/weakest suit
                    longest_suit = max(suits_in_hand.keys(), key=lambda s: len(suits_in_hand[s]))
                    cards = suits_in_hand[longest_suit]
                    discard = min(cards, key=lambda c: self._card_rank(c[1]))
                    return discard, f"Discarding {discard} (can't follow, no trump)"
        else:
            # We're leading - use DD analysis if available
            best_suit = self.get_best_lead(player)
            
            if best_suit and best_suit in suits_in_hand:
                # Lead from best suit according to DD
                cards = suits_in_hand[best_suit]
                # Lead high from strong suit
                best_card = max(cards, key=lambda c: self._card_rank(c[1]))
                tricks = self.get_tricks_for_lead(player, best_suit)
                reason = f"Leading {best_suit} (DD suggests {tricks} tricks)"
                return best_card, reason
            else:
                # Fallback: lead highest card from longest suit
                longest_suit = max(suits_in_hand.keys(), key=lambda s: len(suits_in_hand[s]))
                cards = suits_in_hand[longest_suit]
                best_card = max(cards, key=lambda c: self._card_rank(c[1]))
                return best_card, f"Leading high from longest suit ({longest_suit})"
    
    def _can_beat(self, card, highest_card, led_suit, trump_suit):
        """Check if card can beat the highest card so far"""
        if not highest_card:
            return True
            
        card_suit = card[0]
        high_suit = highest_card[0]
        
        # Trump beats everything
        if trump_suit and trump_suit != 'NT':
            if card_suit == trump_suit and high_suit != trump_suit:
                return True
            if card_suit != trump_suit and high_suit == trump_suit:
                return False
                
        # If different suits (and no trump involved), can't beat
        if card_suit != high_suit:
            return False
            
        # Same suit - compare ranks
        return self._card_rank(card[1]) > self._card_rank(highest_card[1])
    
    def _get_highest_card_in_trick(self, trick, led_suit, trump_suit):
        """Get the currently winning card in the trick"""
        if not trick:
            return None
            
        winning_card = trick[0]['card']
        
        for play in trick[1:]:
            card = play['card']
            if self._can_beat(card, winning_card, led_suit, trump_suit):
                winning_card = card
                
        return winning_card
            
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
        
        # Add interpretation
        lines.append(f"\n💡 Double Dummy Interpretation:")
        lines.append(f"   (Table shows: if PLAYER leads SUIT, how many tricks can DECLARER make)")
        lines.append(f"")
        
        # Parse contract to see who's declaring
        if self.contract:
            # Contract format like "NS 45S" or "EW 3N"
            if 'NS' in self.contract:
                declaring_side = 'NS'
                defending_side = 'EW'
                declarer_players = ['N', 'S']
                defender_players = ['E', 'W']
            elif 'EW' in self.contract:
                declaring_side = 'EW'
                defending_side = 'NS'
                declarer_players = ['E', 'W']
                defender_players = ['N', 'S']
            else:
                declaring_side = None
                
            if declaring_side:
                lines.append(f"   📋 Contract: {declaring_side} declaring")
                lines.append(f"")
                
                # For DEFENDERS: they want to MINIMIZE tricks declarer makes
                # So they should lead the suit that gives declarer the FEWEST tricks
                lines.append(f"   🛡️  Best defensive leads ({defending_side}):")
                for player in defender_players:
                    if player in self.tricks:
                        # Find suit that minimizes declarer's tricks
                        best_def_suit = min(self.tricks[player].keys(), key=lambda s: self.tricks[player][s])
                        min_tricks = self.tricks[player][best_def_suit]
                        lines.append(f"      • {player}: Lead {self._suit_name(best_def_suit)} → limits declarer to {min_tricks} tricks")
                
                lines.append(f"")
                lines.append(f"   ⚔️  If declarer had the lead ({declaring_side}):")
                for player in declarer_players:
                    if player in self.tricks:
                        # Find suit that maximizes declarer's tricks
                        best_decl_suit = max(self.tricks[player].keys(), key=lambda s: self.tricks[player][s])
                        max_tricks = self.tricks[player][best_decl_suit]
                        lines.append(f"      • {player}: Lead {self._suit_name(best_decl_suit)} → makes {max_tricks} tricks")
        else:
            # No contract yet, show general info
            lines.append(f"   ℹ️  Potential trick-taking by partnership:")
            for player in ['N', 'S', 'E', 'W']:
                if player in self.tricks:
                    best_suit = max(self.tricks[player].keys(), key=lambda s: self.tricks[player][s])
                    max_tricks = self.tricks[player][best_suit]
                    partnership = 'NS' if player in ['N', 'S'] else 'EW'
                    lines.append(f"      • {player} leads {self._suit_name(best_suit)}: {partnership} makes {max_tricks} tricks")
                
        return '\n'.join(lines)
    
    def _suit_name(self, suit):
        """Convert suit letter to symbol"""
        suit_names = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
        return suit_names.get(suit, suit)


def recommend_play(dd_data, player, cards_in_hand, current_trick=None, trump_suit=None):
    """
    Convenience function to get play recommendation
    
    Args:
        dd_data: Double dummy data dictionary
        player: 'N', 'S', 'E', or 'W'
        cards_in_hand: List of cards
        current_trick: List of cards played so far this trick
        trump_suit: Trump suit ('S', 'H', 'D', 'C', or 'NT')
        
    Returns:
        Tuple of (recommended_card, reasoning)
    """
    analyzer = DoubleDummyAnalyzer(dd_data)
    return analyzer.analyze_position(player, cards_in_hand, current_trick, trump_suit)

"""
Real-time Double Dummy Solver
Uses endplay library to analyze current position and find best play
"""

from endplay.dds import solve_board, calc_dd_table
from endplay.types import Deal, Player, Card, Denom, Rank

class RealtimeDDS:
    """
    Analyzes bridge positions in real-time using Bo Haglund's DDS engine
    """
    
    def __init__(self):
        pass
    
    def analyze_best_play(self, hands, current_player, trump_suit='NT', played_cards_this_trick=None, declarer=None):
        """
        Find the absolute best card to play from current position
        
        Args:
            hands: Dict of {player: LIN_format_hand} e.g., {'N': 'SAKQJHAKT...', 'E': '...', 'S': '...', 'W': '...'}
            current_player: 'N', 'E', 'S', or 'W'
            trump_suit: 'S', 'H', 'D', 'C', or 'NT'
            played_cards_this_trick: List of {'player': 'W', 'card': 'SA'} for cards already played this trick
            declarer: 'N', 'E', 'S', or 'W' - who is declaring the contract
            
        Returns:
            (best_card, tricks_you_make, reasoning) e.g., ('SA', 10, 'Makes 10 tricks for your side')
        """
        try:
            print(f"🔍 DDS analyzing: player={current_player}, trump={trump_suit}")
            print(f"🔍 DDS hands: {hands}")
            
            # Convert LIN hands to endplay Deal format
            deal = self._lin_to_deal(hands)
            
            # Convert trump suit to Denom and set on deal
            trump_denom = self._suit_to_denom(trump_suit)
            deal.trump = trump_denom
            
            player_map = {'N': Player.north, 'E': Player.east, 'S': Player.south, 'W': Player.west}
            
            # Set who LED this trick (deal.first)
            # If there are cards in current trick, first player is who led
            # Otherwise, current_player is leading
            if played_cards_this_trick and len(played_cards_this_trick) > 0:
                leader = played_cards_this_trick[0]['player']
                deal.first = player_map[leader]
            else:
                deal.first = player_map[current_player]
            
            # Set cards already played this trick
            # Must use deal._data.currentTrickRank and currentTrickSuit arrays
            if played_cards_this_trick:
                print(f"🔍 Adding {len(played_cards_this_trick)} cards to curtrick: {[p['card'] for p in played_cards_this_trick]}")
                from endplay.types import Rank
                for i, play in enumerate(played_cards_this_trick):
                    card = self._card_str_to_endplay(play['card'])
                    # Set rank and suit in the ctypes arrays
                    # Map endplay Rank enum to DDS rank values (2-14)
                    rank_to_dds = {
                        Rank.R2: 2, Rank.R3: 3, Rank.R4: 4, Rank.R5: 5, Rank.R6: 6,
                        Rank.R7: 7, Rank.R8: 8, Rank.R9: 9, Rank.RT: 10, Rank.RJ: 11,
                        Rank.RQ: 12, Rank.RK: 13, Rank.RA: 14
                    }
                    deal._data.currentTrickRank[i] = rank_to_dds[card.rank]
                    deal._data.currentTrickSuit[i] = int(card.suit)
            
            # Use solve_board to get best play
            # solve_board returns an iterable of (Card, tricks) tuples
            result = solve_board(deal)
            
            # Find the card(s) that make the most tricks
            best_card = None
            best_tricks = 0
            for card, tricks in result:
                if tricks > best_tricks:
                    best_tricks = tricks
                    best_card = card
            
            if best_card:
                card_str = self._endplay_card_to_str(best_card)
                
                # Determine declaring side
                if declarer:
                    if declarer in ['N', 'S']:
                        declarer_side = 'NS'
                    else:
                        declarer_side = 'EW'
                else:
                    # Fallback if declarer not provided
                    if current_player in ['N', 'S']:
                        declarer_side = 'NS'
                    else:
                        declarer_side = 'EW'
                
                # Determine current player's side
                if current_player in ['N', 'S']:
                    current_side = 'NS'
                else:
                    current_side = 'EW'
                
                # The DDS returns tricks from declarer's perspective
                # If current player is defending, we want to minimize declarer's tricks
                if current_side == declarer_side:
                    # Playing for declaring side - want to maximize tricks
                    reasoning = f"DDS: Best play makes {best_tricks} tricks for {declarer_side}"
                else:
                    # Playing for defending side - want to minimize declarer's tricks
                    # Total tricks = 13, so defenders make 13 - declarer_tricks
                    defender_tricks = 13 - best_tricks
                    reasoning = f"DDS: Best defense limits {declarer_side} to {best_tricks} tricks ({defender_tricks} for {current_side})"
                
                return card_str, best_tricks, reasoning
            else:
                print(f"⚠️  DDS returned no best cards")
                return None, 0, "DDS: Could not find best play"
                
        except Exception as e:
            import traceback
            print(f"⚠️  DDS Error: {e}")
            print(f"⚠️  DDS Traceback:")
            traceback.print_exc()
            return None, 0, f"DDS Error: {str(e)}"
    
    def _lin_to_deal(self, hands):
        """
        Convert LIN format hands to endplay Deal
        LIN format: 'SAKQJHAKT9D8765C432' (suits separated by suit letters)
        """
        deal = Deal()
        
        for player_str, lin_hand in hands.items():
            # Map NESW to endplay Player enum (which uses lowercase: north, east, south, west)
            player_map = {'N': Player.north, 'E': Player.east, 'S': Player.south, 'W': Player.west}
            player = player_map[player_str]
            
            # Parse LIN format into suits
            suits = {'S': '', 'H': '', 'D': '', 'C': ''}
            current_suit = 'S'
            
            for char in lin_hand:
                if char.upper() in ['S', 'H', 'D', 'C']:
                    current_suit = char.upper()
                elif char in 'AKQJT98765432':
                    suits[current_suit] += char
            
            # Add cards to deal
            for suit_str, ranks in suits.items():
                # Map suit to Denom
                suit_map = {'S': Denom.spades, 'H': Denom.hearts, 'D': Denom.diamonds, 'C': Denom.clubs}
                suit = suit_map[suit_str]
                for rank_char in ranks:
                    # Map rank character to Rank enum
                    rank_map = {'A': Rank.RA, 'K': Rank.RK, 'Q': Rank.RQ, 'J': Rank.RJ, 'T': Rank.RT,
                                '9': Rank.R9, '8': Rank.R8, '7': Rank.R7, '6': Rank.R6, '5': Rank.R5,
                                '4': Rank.R4, '3': Rank.R3, '2': Rank.R2}
                    rank = rank_map[rank_char]
                    card = Card(suit=suit, rank=rank)
                    deal[player].add(card)
        
        # Debug: Check card counts
        card_counts = {p: len(deal[p]) for p in [Player.north, Player.east, Player.south, Player.west]}
        print(f"🔍 Card counts: N={card_counts[Player.north]}, E={card_counts[Player.east]}, S={card_counts[Player.south]}, W={card_counts[Player.west]}")
        
        return deal
    
    def _suit_to_denom(self, suit_str):
        """Convert suit string to endplay Denom"""
        if suit_str == 'NT' or suit_str == 'N':
            return Denom.nt
        elif suit_str == 'S':
            return Denom.spades
        elif suit_str == 'H':
            return Denom.hearts
        elif suit_str == 'D':
            return Denom.diamonds
        elif suit_str == 'C':
            return Denom.clubs
        else:
            return Denom.nt
    
    def _card_str_to_endplay(self, card_str):
        """Convert 'SA' to endplay Card"""
        suit_char = card_str[0]
        rank_char = card_str[1]
        
        # Map suit to Denom
        suit_map = {'S': Denom.spades, 'H': Denom.hearts, 'D': Denom.diamonds, 'C': Denom.clubs}
        suit = suit_map[suit_char]
        
        # Map rank character to Rank enum
        rank_map = {'A': Rank.RA, 'K': Rank.RK, 'Q': Rank.RQ, 'J': Rank.RJ, 'T': Rank.RT,
                    '9': Rank.R9, '8': Rank.R8, '7': Rank.R7, '6': Rank.R6, '5': Rank.R5,
                    '4': Rank.R4, '3': Rank.R3, '2': Rank.R2}
        rank = rank_map[rank_char]
        
        return Card(suit=suit, rank=rank)
    
    def _endplay_card_to_str(self, card):
        """Convert endplay Card to 'SA' format"""
        # Map suit enum to single letter
        suit_map = {
            Denom.spades: 'S',
            Denom.hearts: 'H',
            Denom.diamonds: 'D',
            Denom.clubs: 'C'
        }
        suit_str = suit_map[card.suit]
        rank_str = str(card.rank.abbr)
        return suit_str + rank_str

"""
Decision Engine for Bridge Bot
Uses double dummy analysis to recommend optimal card plays.
"""

from dd_analyzer import DoubleDummyAnalyzer, recommend_play as dd_recommend_play
from realtime_dds import RealtimeDDS

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
        self.realtime_dds = RealtimeDDS()  # Real-time DDS engine
        
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
        # Find the last non-pass bid to get the contract
        contract_bidder = None
        doubled = False
        redoubled = False

        for i in range(len(self.auction) - 1, -1, -1):
            call = self.auction[i]['call'].upper()
            # Check for double/redouble modifiers
            if call in ['X', 'D']:
                doubled = True
            elif call in ['XX', 'DD']:
                redoubled = True
            # Skip passes, doubles, and redoubles - look for actual contract bid
            elif call not in ['P', 'PASS']:
                self.contract = call
                contract_bidder = self.auction[i]['bidder']
                # Append X or XX to contract if doubled/redoubled
                if redoubled:
                    self.contract += 'XX'
                elif doubled:
                    self.contract += 'X'
                break

        if not self.contract:
            return

        # Extract the strain from contract (handle X/XX suffix)
        contract_base = self.contract.replace('XX', '').replace('X', '')

        if 'NT' in contract_base or 'N' == contract_base[-1]:
            strain = 'NT'
        else:
            strain = contract_base[-1]  # S, H, D, or C
        
        # Determine the declaring partnership
        contract_bidder_idx = ['N', 'E', 'S', 'W'].index(contract_bidder)
        partner_idx = (contract_bidder_idx + 2) % 4
        declaring_pair = {contract_bidder, ['N', 'E', 'S', 'W'][partner_idx]}
        
        # Find the FIRST person in the declaring partnership to bid the strain
        for i in range(len(self.auction)):
            call = self.auction[i]['call'].upper()
            bidder = self.auction[i]['bidder']
            
            if bidder in declaring_pair and call not in ['P', 'PASS', 'X', 'XX']:
                # Check if this bid is in the same strain
                if 'NT' in call or 'N' in call:
                    bid_strain = 'NT'
                elif call[-1] in ['S', 'H', 'D', 'C']:
                    bid_strain = call[-1]
                else:
                    continue
                    
                if bid_strain == strain:
                    self.declarer = bidder
                    declarer_idx = ['N', 'E', 'S', 'W'].index(self.declarer)
                    dummy_idx = (declarer_idx + 2) % 4
                    self.dummy = ['N', 'E', 'S', 'W'][dummy_idx]
                    
                    # Lead player is LHO of declarer
                    self.lead_player = ['N', 'E', 'S', 'W'][(declarer_idx + 1) % 4]
                    print(f"🔍 Contract finalized: {self.contract} by {self.declarer} (first to bid {strain}), opening leader: {self.lead_player}")
                    break
                
    def update_card_played(self, player, card):
        """Update state with a played card. Returns (trick_complete, winner, corrected_player)."""
        # If player is unknown ('?'), infer from whose turn it is
        if player not in ['N', 'E', 'S', 'W']:
            # Determine whose turn it is based on current trick
            if len(self.current_trick) == 0:
                # First card of trick - use lead_player
                if self.lead_player:
                    player = self.lead_player
                    print(f"🔍 Player '?' inferred as {player} (leads trick) for card {card}")
                else:
                    print(f"⚠️  Cannot determine player for card {card} - lead_player not set!")
                    return False, None, None
            else:
                # Not first card - determine next player in rotation
                last_player = self.current_trick[-1]['player']
                player_order = ['N', 'E', 'S', 'W']
                last_idx = player_order.index(last_player)
                player = player_order[(last_idx + 1) % 4]
                print(f"🔍 Player '?' inferred as {player} (follows {last_player}) for card {card}")

        # Check if the card actually belongs to dummy (declarer playing from dummy's hand)
        if self.dummy and player != self.dummy:
            # Check if card is in player's hand
            player_hand = self._get_remaining_cards(player, exclude_current_trick=False)
            print(f"🔍 Checking card {card} for player {player}: in_hand={card in player_hand}, hand={player_hand[:5] if len(player_hand) > 5 else player_hand}...")
            if card not in player_hand and self.dummy:
                # Card not in player's hand - check if it's in dummy's hand
                dummy_hand = self._get_remaining_cards(self.dummy, exclude_current_trick=False)
                print(f"🔍 Card {card} not in {player}'s hand, checking dummy ({self.dummy}): in_dummy={card in dummy_hand}, dummy_hand={dummy_hand[:5] if len(dummy_hand) > 5 else dummy_hand}...")
                if card in dummy_hand:
                    print(f"🔍 Card {card} detected in dummy ({self.dummy})'s hand, played by declarer ({self.declarer})")
                    # This card is from dummy's hand, but we record it as dummy playing
                    player = self.dummy
                else:
                    print(f"⚠️  WARNING: Card {card} not found in {player}'s hand OR dummy's hand!")
            
        self.played_cards.append((player, card))
        self.current_trick.append({'player': player, 'card': card})
        
        # If trick is complete (4 cards), determine winner and reset
        if len(self.current_trick) == 4:
            winner = self._determine_trick_winner()
            if winner in ['N', 'S']:
                self.tricks_won['NS'] += 1
            else:
                self.tricks_won['EW'] += 1
            
            # Debug output
            trick_cards = ' '.join([f"{t['player']}:{t['card']}" for t in self.current_trick])
            print(f"🏆 Trick complete: {trick_cards} → {winner} wins")
            
            self.lead_player = winner
            self.current_trick = []
            return True, winner, player
        else:
            # Next player is LHO of current player
            player_idx = ['N', 'E', 'S', 'W'].index(player)
            self.lead_player = ['N', 'E', 'S', 'W'][(player_idx + 1) % 4]
            return False, None, player
            
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
            
        # Get remaining cards for current player
        # exclude_current_trick=True because if they've already played in this trick,
        # that card is no longer available to play again!
        remaining_cards = self._get_remaining_cards(self.lead_player, exclude_current_trick=True)
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
        
        # Build current hands for all players (with cards removed)
        # For DDS: We need to restore cards from the CURRENT trick since they're still "in play"
        # Build set of cards currently in the incomplete trick
        current_trick_cards_by_player = {t['player']: t['card'] for t in self.current_trick}

        current_hands = {}
        for player in ['N', 'S', 'E', 'W']:
            if player in self.hands:
                # Start with original hand
                hand_lin = self.hands[player]
                cards = []

                suits = ['S', 'H', 'D', 'C']
                suit_idx = 0

                for char in hand_lin:
                    if char.upper() in suits:
                        suit_idx = suits.index(char.upper())
                    elif char in 'AKQJT98765432':
                        cards.append(suits[suit_idx] + char)

                original_count = len(cards)

                # Remove ALL played cards (including current trick)
                # Cards in curtrick are removed from hands and go in curtrick only
                removed_count = 0
                for played_player, played_card in self.played_cards:
                    if played_player == player and played_card in cards:
                        cards.remove(played_card)
                        removed_count += 1

                # Debug: Check if card counts make sense
                expected_remaining = original_count - removed_count
                if len(cards) != expected_remaining:
                    print(f"⚠️  Card count mismatch for {player}: expected {expected_remaining}, got {len(cards)}")

                # Convert back to LIN format
                lin_suits = {'S': '', 'H': '', 'D': '', 'C': ''}
                for card in cards:
                    suit = card[0]
                    rank = card[1]
                    lin_suits[suit] += rank
                # Build LIN string
                current_hands[player] = f"S{lin_suits['S']}.H{lin_suits['H']}.D{lin_suits['D']}.C{lin_suits['C']}"
            
        # Debug: Show what we're sending to DDS
        print(f"🔍 DDS: Declarer={self.declarer}, Dummy={self.dummy}, Total played cards={len(self.played_cards)}")

        # Try real-time DDS first (best option - uses current position)
        try:
            best_card, tricks_made, reasoning = self.realtime_dds.analyze_best_play(
                current_hands,
                self.lead_player,
                trump_suit or 'NT',
                self.current_trick,
                self.declarer
            )
            
            # Validate recommended card is actually in hand
            if best_card and best_card in remaining_cards:
                return best_card, reasoning
            elif best_card:
                print(f"⚠️  WARNING: Real-time DDS recommended {best_card} not in hand: {remaining_cards}")
                # Fall through to backup method
        except Exception as e:
            print(f"⚠️  Real-time DDS error: {e}")
            # Fall through to backup method
            
        # Fallback: Use static DD analysis (opening lead only, less accurate mid-hand)
        if self.dd_data:
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
                    print(f"⚠️  WARNING: Static DD recommended {card} not in hand: {remaining_cards}")
                    card = remaining_cards[0]
                    reasoning = f"Playing {card} (fallback due to logic error)"
                
                return card, reasoning
            except Exception as e:
                return None, f"Error analyzing position: {str(e)}"
        
        # Last resort: just play first card
        return remaining_cards[0], f"Playing {remaining_cards[0]} (no DD analysis available)"
            
    def _get_remaining_cards(self, player, exclude_current_trick=False):
        """Get list of cards still in player's hand.
        
        Args:
            player: Player position ('N', 'E', 'S', 'W')
            exclude_current_trick: If True, also exclude cards this player has played in current trick
                                  (for validation). If False, keep them (for DDS).
        """
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
        
        # Optionally exclude cards this player played in current trick
        if exclude_current_trick:
            for trick_play in self.current_trick:
                if trick_play['player'] == player and trick_play['card'] in cards:
                    cards.remove(trick_play['card'])
                
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

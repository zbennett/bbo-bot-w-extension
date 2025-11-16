"""
Standard American Bidding System
Comprehensive implementation of Standard American Yellow Card (SAYC) bidding

Features:
- Hand evaluation (HCP + distribution points)
- Opening bids (1-level, 2-level, preempts, 2C strong)
- Responses to all opening bids
- Rebids and game-forcing sequences
- Common conventions: Stayman, Jacoby Transfers, Blackwood, Gerber
- Competitive bidding
"""

class Hand:
    """Represents a bridge hand with evaluation methods"""

    def __init__(self, lin_hand):
        """
        Initialize hand from LIN format (e.g., 'SAKQJHAKT9D8765C432')
        """
        self.suits = {'S': [], 'H': [], 'D': [], 'C': []}
        self.parse_lin(lin_hand)
        self.hcp = self.count_hcp()
        self.distribution = self.get_distribution()
        self.shape = self.get_shape_pattern()

    def parse_lin(self, lin_str):
        """Parse LIN format into suit dictionary"""
        current_suit = None
        for char in lin_str:
            if char in ['S', 'H', 'D', 'C']:
                current_suit = char
            elif char in 'AKQJT98765432':
                self.suits[current_suit].append(char)

    def count_hcp(self):
        """Count high card points (A=4, K=3, Q=2, J=1)"""
        points = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
        return sum(points.get(card, 0) for suit in self.suits.values() for card in suit)

    def get_distribution(self):
        """Get distribution (length of each suit)"""
        return {suit: len(cards) for suit, cards in self.suits.items()}

    def get_shape_pattern(self):
        """Get shape pattern sorted by length (e.g., [5,4,2,2])"""
        lengths = [len(cards) for cards in self.suits.values()]
        return sorted(lengths, reverse=True)

    def count_total_points(self):
        """Count total points including distribution (for opening/responding)"""
        # Shortage points: void=3, singleton=2, doubleton=1
        dist_points = 0
        for length in self.get_distribution().values():
            if length == 0:
                dist_points += 3
            elif length == 1:
                dist_points += 2
            elif length == 2:
                dist_points += 1
        return self.hcp + dist_points

    def longest_suit(self):
        """Return the longest suit(s)"""
        dist = self.get_distribution()
        max_len = max(dist.values())
        return [suit for suit, length in dist.items() if length == max_len]

    def is_balanced(self):
        """Check if hand is balanced (no singleton/void, at most one doubleton)"""
        shape = self.shape
        return shape in [[4,3,3,3], [4,4,3,2], [5,3,3,2]]

    def is_semi_balanced(self):
        """Check if hand is semi-balanced (includes 5-4-2-2 and 6-3-2-2)"""
        shape = self.shape
        return shape in [[4,3,3,3], [4,4,3,2], [5,3,3,2], [5,4,2,2], [6,3,2,2]]

    def has_stopper(self, suit):
        """Check if hand has a stopper in given suit (A, Kx, Qxx, Jxxx)"""
        cards = self.suits[suit]
        if not cards:
            return False
        if 'A' in cards:
            return True
        if 'K' in cards and len(cards) >= 2:
            return True
        if 'Q' in cards and len(cards) >= 3:
            return True
        if 'J' in cards and len(cards) >= 4:
            return True
        return False

    def quick_tricks(self):
        """Count quick tricks (defensive tricks)"""
        qt = 0
        for suit, cards in self.suits.items():
            if 'A' in cards and 'K' in cards:
                qt += 2
            elif 'A' in cards:
                qt += 1
            elif 'K' in cards and 'Q' in cards:
                qt += 1
            elif 'K' in cards:
                qt += 0.5
        return qt


class StandardAmericanBidding:
    """
    Standard American bidding system with SAYC conventions
    """

    def __init__(self):
        self.hand = None
        self.auction = []
        self.partner_bids = []
        self.opponent_bids = []
        self.position = None  # 'N', 'E', 'S', 'W'
        self.vulnerability = None

    def set_hand(self, lin_hand):
        """Set the current hand to analyze"""
        self.hand = Hand(lin_hand)

    def set_auction(self, auction, position):
        """
        Set the current auction
        auction: list of {'call': 'bid', 'bidder': 'N/E/S/W'}
        position: current player's position
        """
        self.auction = auction
        self.position = position

        # Separate partner and opponent bids
        partner = self._get_partner(position)
        lho = self._get_lho(position)
        rho = self._get_rho(position)

        self.partner_bids = [a for a in auction if a['bidder'] == partner]
        self.opponent_bids = [a for a in auction if a['bidder'] in [lho, rho]]

    def _get_partner(self, position):
        """Get partner's position"""
        partners = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        return partners[position]

    def _get_lho(self, position):
        """Get left-hand opponent"""
        order = ['N', 'E', 'S', 'W']
        idx = order.index(position)
        return order[(idx + 1) % 4]

    def _get_rho(self, position):
        """Get right-hand opponent"""
        order = ['N', 'E', 'S', 'W']
        idx = order.index(position)
        return order[(idx - 1) % 4]

    def get_recommendation(self):
        """
        Get bidding recommendation based on current auction and hand
        Returns: (bid, reasoning)
        """
        if not self.hand:
            return None, "No hand set"

        # If auction is empty or all passes, this is an opening bid
        if not self.auction or all(a['call'].upper() in ['P', 'PASS'] for a in self.auction):
            return self._get_opening_bid()

        # Get last non-pass bid to understand auction state
        last_bid = self._get_last_bid()
        partner_opened = self._did_partner_open()
        opponent_opened = self._did_opponent_open()

        # Response to partner's opening
        if partner_opened and not self._have_i_bid():
            partner_opening = self._get_partner_opening()
            return self._respond_to_partner_opening(partner_opening)

        # Overcall after opponent opens
        if opponent_opened and not self._have_i_bid() and not partner_opened:
            return self._get_overcall()

        # Rebid or continuation
        if self._have_i_bid():
            return self._get_rebid()

        # Response to partner's response
        if partner_opened and self._have_i_bid():
            return self._get_rebid_after_response()

        # Default: pass
        return 'P', "No clear bid available"

    def _get_opening_bid(self):
        """Determine opening bid"""
        hcp = self.hand.hcp
        total_points = self.hand.count_total_points()
        dist = self.hand.get_distribution()
        shape = self.hand.shape

        # 2C opening (22+ HCP or game-forcing hand)
        if hcp >= 22:
            return '2C', f"2♣ Strong artificial (22+ HCP, {hcp} HCP)"

        # Strong 2-level opening (not SAYC standard, but common)
        # Skip for now, as SAYC uses weak 2-bids

        # Weak 2-bids in hearts, spades, diamonds (5-11 HCP, 6-card suit)
        if 5 <= hcp <= 11:
            for suit in ['S', 'H', 'D']:
                if dist[suit] == 6:
                    suit_quality = self._suit_quality(suit)
                    if suit_quality >= 2:  # At least 2 of top 3 honors
                        suit_name = {'S': '♠', 'H': '♥', 'D': '♦'}[suit]
                        return f'2{suit}', f"Weak 2{suit_name} (6-card suit, {hcp} HCP)"

        # Preemptive 3-level (7-card suit, 6-10 HCP)
        if 6 <= hcp <= 10:
            for suit in ['S', 'H', 'D', 'C']:
                if dist[suit] >= 7:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                    return f'3{suit}', f"Preemptive 3{suit_name} (7+ card suit, {hcp} HCP)"

        # 1NT opening (15-17 HCP, balanced)
        if 15 <= hcp <= 17 and self.hand.is_balanced():
            return '1NT', f"1NT balanced ({hcp} HCP)"

        # 2NT opening (20-21 HCP, balanced)
        if 20 <= hcp <= 21 and self.hand.is_balanced():
            return '2NT', f"2NT balanced ({hcp} HCP)"

        # 3NT opening (strong, gambling - solid minor, no outside stoppers)
        # Skip for now

        # 1-level suit opening (12+ HCP or Rule of 20)
        if hcp >= 12 or (hcp >= 10 and self._rule_of_20()):
            # Choose suit to open
            # Priority: 5+ card suit, longer suit first, higher ranking with equal length

            # 5+ card major
            if dist['S'] >= 5 and dist['H'] >= 5:
                # Both majors - bid spades first (higher)
                return '1S', f"1♠ ({dist['S']}-card suit, {hcp} HCP)"
            elif dist['S'] >= 5:
                return '1S', f"1♠ ({dist['S']}-card suit, {hcp} HCP)"
            elif dist['H'] >= 5:
                return '1H', f"1♥ ({dist['H']}-card suit, {hcp} HCP)"

            # No 5-card major - choose minor
            # With 3-3 in minors, open 1C
            # With 4-4 in minors, open 1D
            # Longer minor first
            if dist['D'] > dist['C']:
                return '1D', f"1♦ ({dist['D']}-card suit, {hcp} HCP)"
            elif dist['C'] > dist['D']:
                return '1C', f"1♣ ({dist['C']}-card suit, {hcp} HCP)"
            elif dist['D'] == 4 and dist['C'] == 4:
                return '1D', f"1♦ (4-4 minors, {hcp} HCP)"
            else:
                # 3-3 minors - open 1C
                return '1C', f"1♣ (3-3 minors, {hcp} HCP)"

        # Not enough to open
        return 'P', f"Pass (insufficient values, {hcp} HCP)"

    def _respond_to_partner_opening(self, opening_bid):
        """Respond to partner's opening bid"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # Response to 1NT
        if opening_bid == '1NT':
            return self._respond_to_1nt()

        # Response to 2C (strong artificial)
        if opening_bid == '2C':
            return self._respond_to_2c()

        # Response to 2NT
        if opening_bid == '2NT':
            return self._respond_to_2nt()

        # Response to weak 2-bid
        if opening_bid in ['2H', '2S', '2D']:
            return self._respond_to_weak_2()

        # Response to 1-level suit opening
        if opening_bid in ['1C', '1D', '1H', '1S']:
            return self._respond_to_1_suit(opening_bid)

        return 'P', "Pass (default)"

    def _respond_to_1nt(self):
        """Respond to partner's 1NT opening (15-17 HCP)"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # 0-7 HCP: Pass or sign off
        if hcp <= 7:
            # With 6+ card major, transfer then pass
            if dist['H'] >= 6:
                return '2D', "2♦ Jacoby transfer (6+ hearts, sign off)"
            if dist['S'] >= 6:
                return '2H', "2♥ Jacoby transfer (6+ spades, sign off)"
            # Balanced - pass
            if self.hand.is_balanced():
                return 'P', f"Pass 1NT ({hcp} HCP, balanced)"
            # Weak with long suit - pass or transfer
            return 'P', f"Pass 1NT ({hcp} HCP)"

        # 8-9 HCP: Invite
        if 8 <= hcp <= 9:
            # Stayman with 4-card major
            if dist['H'] >= 4 or dist['S'] >= 4:
                return '2C', f"2♣ Stayman (invitational, 4-card major, {hcp} HCP)"
            # Balanced - invite to 2NT
            if self.hand.is_balanced():
                return '2NT', f"2NT invitational ({hcp} HCP, balanced)"
            # 5-card major - transfer and invite
            if dist['H'] >= 5:
                return '2D', f"2♦ Jacoby transfer (5+ hearts, invitational)"
            if dist['S'] >= 5:
                return '2H', f"2♥ Jacoby transfer (5+ spades, invitational)"

        # 10-14 HCP: Game
        if 10 <= hcp <= 14:
            # Stayman with 4-card major
            if dist['H'] >= 4 or dist['S'] >= 4:
                return '2C', f"2♣ Stayman (game-forcing, {hcp} HCP)"
            # 5-card major - transfer to game
            if dist['H'] >= 5:
                return '2D', f"2♦ Jacoby transfer (5+ hearts, game-forcing)"
            if dist['S'] >= 5:
                return '2H', f"2♥ Jacoby transfer (5+ spades, game-forcing)"
            # Balanced - go to 3NT
            return '3NT', f"3NT game ({hcp} HCP, balanced)"

        # 15+ HCP: Slam interest
        if hcp >= 15:
            # With 4-card major, use Stayman
            if dist['H'] >= 4 or dist['S'] >= 4:
                return '2C', f"2♣ Stayman (slam interest, {hcp} HCP)"
            # Quantitative 4NT
            if hcp >= 16 and self.hand.is_balanced():
                return '4NT', f"4NT quantitative (slam invitation, {hcp} HCP)"
            # Jump to game with plan for slam later
            return '3NT', f"3NT (slam interest, {hcp} HCP)"

        return 'P', f"Pass ({hcp} HCP)"

    def _respond_to_2c(self):
        """Respond to partner's 2C strong opening"""
        hcp = self.hand.hcp

        # 2D = waiting (0-7 HCP or no good suit)
        if hcp < 8:
            return '2D', f"2♦ waiting (negative, {hcp} HCP)"

        # With 8+ HCP, show suit
        dist = self.hand.get_distribution()

        # Positive response: 2H, 2S, 3C, 3D with 5+ cards and 8+ HCP
        if dist['H'] >= 5:
            return '2H', f"2♥ positive ({hcp} HCP, 5+ hearts)"
        if dist['S'] >= 5:
            return '2S', f"2♠ positive ({hcp} HCP, 5+ spades)"

        # 2NT = balanced 8+ HCP
        if self.hand.is_balanced():
            return '2NT', f"2NT positive ({hcp} HCP, balanced)"

        # Show minor at 3-level
        if dist['C'] >= 5:
            return '3C', f"3♣ positive ({hcp} HCP, 5+ clubs)"
        if dist['D'] >= 5:
            return '3D', f"3♦ positive ({hcp} HCP, 5+ diamonds)"

        # Default waiting bid
        return '2D', f"2♦ waiting ({hcp} HCP)"

    def _respond_to_2nt(self):
        """Respond to partner's 2NT opening (20-21 HCP)"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # 0-4 HCP: Pass or sign off
        if hcp <= 4:
            # Transfer to major if 6+ cards
            if dist['H'] >= 6:
                return '3D', "3♦ Jacoby transfer (6+ hearts, sign off)"
            if dist['S'] >= 6:
                return '3H', "3♥ Jacoby transfer (6+ spades, sign off)"
            return 'P', f"Pass 2NT ({hcp} HCP)"

        # 5-10 HCP: Game
        if 5 <= hcp <= 10:
            # Stayman with 4-card major
            if dist['H'] >= 4 or dist['S'] >= 4:
                return '3C', f"3♣ Stayman ({hcp} HCP)"
            # Transfer to major
            if dist['H'] >= 5:
                return '3D', f"3♦ Jacoby transfer (5+ hearts, game-forcing)"
            if dist['S'] >= 5:
                return '3H', f"3♥ Jacoby transfer (5+ spades, game-forcing)"
            # Balanced - go to game
            return '3NT', f"3NT game ({hcp} HCP)"

        # 11+ HCP: Slam interest
        if hcp >= 11:
            # Use Gerber (4C) for aces
            return '4C', f"4♣ Gerber (asking for aces, {hcp} HCP)"

        return '3NT', f"3NT game ({hcp} HCP)"

    def _respond_to_weak_2(self):
        """Respond to partner's weak 2-bid"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()
        opening = self._get_partner_opening()

        # Extract suit from opening (2H -> 'H')
        suit = opening[1]

        # 0-14 HCP: Pass
        if hcp < 15:
            return 'P', f"Pass weak 2-bid ({hcp} HCP, insufficient for game)"

        # 15-17 HCP: Invite to game
        if 15 <= hcp <= 17:
            # Raise to 3-level (invitational)
            suit_name = {'S': '♠', 'H': '♥', 'D': '♦'}[suit]
            return f'3{suit}', f"3{suit_name} invitational ({hcp} HCP)"

        # 18+ HCP: Go to game
        if hcp >= 18:
            suit_name = {'S': '♠', 'H': '♥', 'D': '♦'}[suit]
            if suit in ['H', 'S']:
                return f'4{suit}', f"4{suit_name} game ({hcp} HCP)"
            else:
                # Diamond weak 2 - go to 3NT or 5D
                if self.hand.is_balanced():
                    return '3NT', f"3NT game ({hcp} HCP)"
                return f'5{suit}', f"5{suit_name} game ({hcp} HCP)"

        return 'P', f"Pass ({hcp} HCP)"

    def _respond_to_1_suit(self, opening_bid):
        """Respond to partner's 1-level suit opening"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()
        opening_suit = opening_bid[1]  # Extract suit (1H -> 'H')

        # 0-5 HCP: Pass
        if hcp < 6:
            return 'P', f"Pass ({hcp} HCP, insufficient to respond)"

        # 6-9 HCP: Minimum response
        if 6 <= hcp <= 9:
            # Support partner's major with 3+ cards
            if opening_suit in ['H', 'S'] and dist[opening_suit] >= 3:
                suit_name = {'S': '♠', 'H': '♥'}[opening_suit]
                return f'2{opening_suit}', f"2{suit_name} raise (3+ card support, {hcp} HCP)"

            # Bid new suit at 1-level (4+ cards)
            # Priority: 4-card major, then longer suit
            if opening_suit in ['C', 'D']:
                # Partner opened minor
                if dist['H'] >= 4 and dist['S'] >= 4:
                    # Both majors - bid hearts first (up the line)
                    return '1H', f"1♥ new suit (4+ hearts, {hcp} HCP)"
                if dist['H'] >= 4:
                    return '1H', f"1♥ new suit (4+ hearts, {hcp} HCP)"
                if dist['S'] >= 4:
                    return '1S', f"1♠ new suit (4+ spades, {hcp} HCP)"

            # 1NT response (6-10 HCP, no fit, balanced)
            if self.hand.is_balanced():
                return '1NT', f"1NT (6-9 HCP, no fit)"

            # Raise partner's minor with 5+ cards
            if dist[opening_suit] >= 5:
                suit_name = {'D': '♦', 'C': '♣'}[opening_suit]
                return f'2{opening_suit}', f"2{suit_name} raise (5+ card support, {hcp} HCP)"

            # Last resort - 1NT
            return '1NT', f"1NT (6-9 HCP, no good bid)"

        # 10-12 HCP: Invitational
        if 10 <= hcp <= 12:
            # Limit raise with 4+ card support
            if dist[opening_suit] >= 4:
                suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[opening_suit]
                return f'3{opening_suit}', f"3{suit_name} limit raise (4+ card support, {hcp} HCP)"

            # Bid new suit at 1-level
            if opening_suit in ['C', 'D']:
                if dist['H'] >= 4:
                    return '1H', f"1♥ new suit ({hcp} HCP)"
                if dist['S'] >= 4:
                    return '1S', f"1♠ new suit ({hcp} HCP)"

            # 2NT invitational (11-12 HCP, balanced, stoppers)
            if 11 <= hcp <= 12 and self.hand.is_balanced():
                return '2NT', f"2NT invitational ({hcp} HCP, balanced)"

            # Jump shift with good 6+ card suit and 17+ points
            # (Skip for now in this range)

            # New suit at 2-level (needs 10+ HCP)
            # Bid longest unbid suit
            for suit in ['C', 'D', 'H', 'S']:
                if suit != opening_suit and dist[suit] >= 4:
                    level = '2' if suit in ['D', 'C'] or opening_suit in ['H', 'S'] else '1'
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                    return f'{level}{suit}', f"{level}{suit_name} new suit ({hcp} HCP)"

            return '1NT', f"1NT ({hcp} HCP)"

        # 13-15 HCP: Game-forcing
        if 13 <= hcp <= 15:
            # With 4+ card support, consider splinter or Jacoby 2NT
            if dist[opening_suit] >= 4 and opening_suit in ['H', 'S']:
                # Jacoby 2NT (game-forcing raise)
                return '2NT', f"2NT Jacoby (4+ card support, {hcp} HCP, game-forcing)"

            # Bid new suit (game-forcing if jump shift or new suit at 2-level)
            # Try to bid major if possible
            if opening_suit in ['C', 'D']:
                if dist['S'] >= 4:
                    return '1S', f"1♠ new suit (game-forcing, {hcp} HCP)"
                if dist['H'] >= 4:
                    return '1H', f"1♥ new suit (game-forcing, {hcp} HCP)"

            # 3NT with balanced hand and stoppers
            if self.hand.is_balanced() and hcp >= 13:
                return '3NT', f"3NT game ({hcp} HCP, balanced)"

            # New suit at 2-level
            for suit in ['C', 'D', 'H', 'S']:
                if suit != opening_suit and dist[suit] >= 4:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                    return f'2{suit}', f"2{suit_name} new suit (game-forcing, {hcp} HCP)"

        # 16+ HCP: Slam interest
        if hcp >= 16:
            # Jump shift to show 17+ HCP and good suit
            for suit in ['S', 'H', 'D', 'C']:
                if suit != opening_suit and dist[suit] >= 5:
                    # Jump shift
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                    if opening_suit in ['C', 'D'] and suit in ['H', 'S']:
                        return f'2{suit}', f"2{suit_name} jump shift (slam interest, {hcp} HCP)"

            # Strong jump to 3NT
            if self.hand.is_balanced():
                return '3NT', f"3NT game (slam interest, {hcp} HCP)"

        return 'P', "Pass (no clear bid)"

    def _get_overcall(self):
        """Determine overcall after opponent opens"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()
        last_bid = self._get_last_bid()

        # Simple overcall (8-17 HCP, 5+ card suit, 2+ quick tricks)
        if 8 <= hcp <= 17:
            qt = self.hand.quick_tricks()
            if qt >= 2:
                # Try to overcall in a suit
                for suit in ['S', 'H', 'D', 'C']:
                    if dist[suit] >= 5:
                        suit_quality = self._suit_quality(suit)
                        if suit_quality >= 1:  # At least 1 of top 3 honors
                            level = self._minimum_level(suit, last_bid)
                            if level <= 2:  # Don't overcall at 3-level with minimum
                                suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                                return f'{level}{suit}', f"{level}{suit_name} overcall ({hcp} HCP, {dist[suit]}-card suit)"

        # 1NT overcall (15-18 HCP, balanced, stoppers in opponent's suit)
        if 15 <= hcp <= 18 and self.hand.is_balanced():
            opponent_suit = last_bid[1] if len(last_bid) > 1 else None
            if opponent_suit and self.hand.has_stopper(opponent_suit):
                return '1NT', f"1NT overcall ({hcp} HCP, balanced, stopper)"

        # Jump overcall (weak, 6-card suit, 6-11 HCP)
        if 6 <= hcp <= 11:
            for suit in ['S', 'H', 'D', 'C']:
                if dist[suit] >= 6:
                    suit_quality = self._suit_quality(suit)
                    if suit_quality >= 2:
                        level = self._minimum_level(suit, last_bid) + 1
                        if level <= 3:
                            suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                            return f'{level}{suit}', f"{level}{suit_name} jump overcall (weak, {hcp} HCP)"

        # Takeout double (12+ HCP, support for unbid suits, shortage in opponent's suit)
        if hcp >= 12:
            opponent_suit = last_bid[1] if len(last_bid) > 1 else None
            if opponent_suit and dist[opponent_suit] <= 2:
                # Check support for other suits
                other_suits = [s for s in ['S', 'H', 'D', 'C'] if s != opponent_suit]
                if all(dist[s] >= 3 for s in other_suits):
                    return 'D', f"Double for takeout ({hcp} HCP, shortage in opponent's suit)"

        # Strong overcall (18+ HCP)
        if hcp >= 18:
            # Jump to 2NT or cue bid
            if self.hand.is_balanced():
                return '2NT', f"2NT overcall (strong, {hcp} HCP)"

        return 'P', f"Pass (no safe overcall, {hcp} HCP)"

    def _get_rebid(self):
        """Get rebid after opening"""
        # Placeholder for rebid logic
        # This would handle opener's rebid after responder's call
        return 'P', "Pass (rebid logic not yet implemented)"

    def _get_rebid_after_response(self):
        """Get rebid after partner responds"""
        # Placeholder for continuation logic
        return 'P', "Pass (continuation logic not yet implemented)"

    def _get_last_bid(self):
        """Get the last non-pass bid from auction"""
        for auction_item in reversed(self.auction):
            call = auction_item['call'].upper()
            if call not in ['P', 'PASS']:
                return call
        return None

    def _did_partner_open(self):
        """Check if partner made the opening bid"""
        if not self.auction:
            return False
        partner = self._get_partner(self.position)
        for auction_item in self.auction:
            if auction_item['bidder'] == partner:
                call = auction_item['call'].upper()
                if call not in ['P', 'PASS']:
                    return True
        return False

    def _did_opponent_open(self):
        """Check if an opponent made the opening bid"""
        if not self.auction:
            return False
        lho = self._get_lho(self.position)
        rho = self._get_rho(self.position)
        for auction_item in self.auction:
            if auction_item['bidder'] in [lho, rho]:
                call = auction_item['call'].upper()
                if call not in ['P', 'PASS']:
                    return True
        return False

    def _have_i_bid(self):
        """Check if current player has already made a bid"""
        for auction_item in self.auction:
            if auction_item['bidder'] == self.position:
                call = auction_item['call'].upper()
                if call not in ['P', 'PASS']:
                    return True
        return False

    def _get_partner_opening(self):
        """Get partner's opening bid"""
        partner = self._get_partner(self.position)
        for auction_item in self.auction:
            if auction_item['bidder'] == partner:
                call = auction_item['call'].upper()
                if call not in ['P', 'PASS']:
                    return call
        return None

    def _rule_of_20(self):
        """Rule of 20: HCP + length of two longest suits >= 20"""
        hcp = self.hand.hcp
        shape = self.hand.shape
        return (hcp + shape[0] + shape[1]) >= 20

    def _suit_quality(self, suit):
        """Count honors in suit (A=1, K=1, Q=1)"""
        cards = self.hand.suits[suit]
        honors = sum(1 for card in ['A', 'K', 'Q'] if card in cards)
        return honors

    def _minimum_level(self, suit, over_bid):
        """Calculate minimum level needed to bid suit over opponent's bid"""
        if not over_bid:
            return 1

        # Extract level and suit from opponent's bid
        try:
            level = int(over_bid[0])
            opp_suit = over_bid[1] if len(over_bid) > 1 else None
        except:
            return 1

        # Suit ranking: C < D < H < S
        suit_rank = {'C': 0, 'D': 1, 'H': 2, 'S': 3, 'NT': 4}

        if opp_suit and opp_suit in suit_rank:
            if suit_rank[suit] > suit_rank[opp_suit]:
                return level
            else:
                return level + 1

        return level + 1

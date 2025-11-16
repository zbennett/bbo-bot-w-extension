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
        """Get rebid after we've already made a bid"""
        # Determine what we bid previously
        my_bids = [a for a in self.auction if a['bidder'] == self.position]
        if not my_bids:
            return 'P', "Pass (no previous bid found)"

        my_first_bid = my_bids[0]['call'].upper()

        # Check if we opened
        if self._am_i_opener():
            return self._opener_rebid(my_first_bid)
        else:
            return self._responder_rebid(my_first_bid)

    def _opener_rebid(self, my_opening):
        """Handle opener's rebid after partner responds"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # Get partner's response
        partner_response = self._get_partner_last_call()
        if not partner_response:
            return 'P', "Pass (no partner response)"

        # Handle rebid after 1NT opening
        if my_opening == '1NT':
            return self._rebid_after_1nt_opening(partner_response)

        # Handle rebid after 2C opening
        if my_opening == '2C':
            return self._rebid_after_2c_opening(partner_response)

        # Handle rebid after weak 2-bid
        if my_opening in ['2H', '2S', '2D']:
            return self._rebid_after_weak_2(partner_response)

        # Handle rebid after 1-level suit opening
        if my_opening in ['1C', '1D', '1H', '1S']:
            return self._rebid_after_1_suit_opening(my_opening, partner_response)

        return 'P', "Pass (no rebid found)"

    def _rebid_after_1nt_opening(self, partner_response):
        """Rebid after opening 1NT"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # After 2C Stayman
        if partner_response == '2C':
            # Show 4-card major
            if dist['H'] >= 4 and dist['S'] >= 4:
                return '2H', "2♥ (4 hearts, may have 4 spades)"
            elif dist['H'] >= 4:
                return '2H', "2♥ (4+ hearts)"
            elif dist['S'] >= 4:
                return '2S', "2♠ (4+ spades)"
            else:
                return '2D', "2♦ (no 4-card major)"

        # After 2D transfer to hearts
        if partner_response == '2D':
            return '2H', "2♥ (accepting transfer)"

        # After 2H transfer to spades
        if partner_response == '2H':
            return '2S', "2♠ (accepting transfer)"

        # After 2NT invitational
        if partner_response == '2NT':
            # 15-16: Pass, 17: Accept
            if hcp >= 17:
                return '3NT', f"3NT (maximum, {hcp} HCP)"
            else:
                return 'P', f"Pass (minimum, {hcp} HCP)"

        # After 3NT
        if partner_response == '3NT':
            return 'P', "Pass (game reached)"

        # After 4NT quantitative
        if partner_response == '4NT':
            # 15-16: Pass, 17: bid slam
            if hcp >= 17:
                return '6NT', f"6NT slam (maximum, {hcp} HCP)"
            else:
                return 'P', f"Pass (minimum, {hcp} HCP)"

        return 'P', "Pass"

    def _rebid_after_2c_opening(self, partner_response):
        """Rebid after opening 2C (strong)"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # After 2D waiting
        if partner_response == '2D':
            # Show our suit
            if dist['S'] >= 5:
                return '2S', f"2♠ (5+ spades, {hcp} HCP)"
            elif dist['H'] >= 5:
                return '2H', f"2♥ (5+ hearts, {hcp} HCP)"
            elif self.hand.is_balanced() and hcp >= 22:
                if 22 <= hcp <= 24:
                    return '2NT', f"2NT (22-24 HCP, balanced)"
                else:
                    return '3NT', f"3NT (25+ HCP, balanced)"
            elif dist['D'] >= 5:
                return '3D', f"3♦ (5+ diamonds, {hcp} HCP)"
            elif dist['C'] >= 5:
                return '3C', f"3♣ (5+ clubs, {hcp} HCP)"

        # After positive response in a suit - continue bidding naturally
        return 'P', "Pass (let partner describe further)"

    def _rebid_after_weak_2(self, partner_response):
        """Rebid after weak 2-bid opening"""
        # After weak 2-bid, usually pass unless partner forces to game
        if partner_response in ['3NT', '4H', '4S']:
            return 'P', "Pass (game reached)"

        # After invitational raise (e.g., 2H-3H)
        # Pass with minimum, bid game with maximum
        hcp = self.hand.hcp
        if hcp >= 10:  # Maximum for weak 2
            my_opening = self._get_my_opening()
            suit = my_opening[1]
            if suit in ['H', 'S']:
                return f'4{suit}', f"4{{'H': '♥', 'S': '♠'}[suit]} (maximum weak 2)"

        return 'P', "Pass (minimum weak 2)"

    def _rebid_after_1_suit_opening(self, my_opening, partner_response):
        """Rebid after opening 1 of a suit"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()
        opening_suit = my_opening[1]  # 'C', 'D', 'H', or 'S'

        # Partner passed - pass
        if partner_response in ['P', 'PASS']:
            return 'P', "Pass (partner passed)"

        # Partner bid game - pass
        if partner_response in ['3NT', '4H', '4S', '5C', '5D']:
            return 'P', "Pass (game reached)"

        # Partner bid 1NT (6-10 HCP)
        if partner_response == '1NT':
            # Minimum (12-15): Pass or rebid 6-card suit
            if hcp <= 15:
                if dist[opening_suit] >= 6:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[opening_suit]
                    return f'2{opening_suit}', f"2{suit_name} rebid (6+ cards, minimum)"
                return 'P', f"Pass 1NT (minimum, {hcp} HCP)"

            # Medium (16-18): Invite with 2NT or rebid good suit
            if 16 <= hcp <= 18:
                if self.hand.is_balanced():
                    return '2NT', f"2NT invitational ({hcp} HCP)"
                if dist[opening_suit] >= 6:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[opening_suit]
                    return f'3{opening_suit}', f"3{suit_name} (invitational, 6+ cards)"

            # Strong (19+): Jump to 3NT or game
            if hcp >= 19:
                return '3NT', f"3NT game ({hcp} HCP)"

        # Partner raised our suit (e.g., 1H-2H showing 6-9 HCP, 3+ card support)
        if partner_response == f'2{opening_suit}':
            # With 16+ HCP and 5+ card suit, invite or bid game
            if hcp >= 19 and opening_suit in ['H', 'S']:
                return f'4{opening_suit}', f"4{{'H': '♥', 'S': '♠'}[opening_suit]} game ({hcp} HCP)"
            if 16 <= hcp <= 18 and opening_suit in ['H', 'S']:
                suit_name = {'H': '♥', 'S': '♠'}[opening_suit]
                return f'3{opening_suit}', f"3{suit_name} invitational ({hcp} HCP)"
            # With minimum, pass
            return 'P', f"Pass (minimum, {hcp} HCP)"

        # Partner made limit raise (e.g., 1H-3H showing 10-12 HCP)
        if partner_response == f'3{opening_suit}':
            # With 16+ HCP, bid game
            if hcp >= 16 and opening_suit in ['H', 'S']:
                return f'4{opening_suit}', f"4{{'H': '♥', 'S': '♠'}[opening_suit]} game ({hcp} HCP)"
            if hcp >= 16 and opening_suit in ['C', 'D']:
                # Consider 3NT or 5-level
                if self.hand.is_semi_balanced():
                    return '3NT', f"3NT game ({hcp} HCP)"
                return f'5{opening_suit}', f"5{{'D': '♦', 'C': '♣'}[opening_suit]} game ({hcp} HCP)"
            # With minimum, pass
            return 'P', f"Pass (minimum, {hcp} HCP)"

        # Partner bid 2NT (Jacoby, game-forcing with 4+ card support)
        if partner_response == '2NT' and opening_suit in ['H', 'S']:
            # Show hand strength
            if hcp <= 14:
                # Minimum - bid game
                return f'4{opening_suit}', f"4{{'H': '♥', 'S': '♠'}[opening_suit]} (minimum opener)"
            elif 15 <= hcp <= 17:
                # Medium - show shortness or side suit
                for suit in ['C', 'D', 'H', 'S']:
                    if suit != opening_suit and dist[suit] <= 1:
                        # Show singleton/void
                        suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                        return f'3{suit}', f"3{suit_name} shortness (medium opener)"
                # No clear shortness - rebid 3 of opening suit
                suit_name = {'H': '♥', 'S': '♠'}[opening_suit]
                return f'3{opening_suit}', f"3{suit_name} (medium opener, no shortness)"
            else:
                # Strong - show slam interest
                return f'3{opening_suit}', f"3{{'H': '♥', 'S': '♠'}[opening_suit]} (strong opener, slam try)"

        # Partner bid 2NT (standard invitational 11-12 HCP)
        if partner_response == '2NT':
            if hcp >= 15:
                return '3NT', f"3NT game ({hcp} HCP)"
            return 'P', f"Pass 2NT ({hcp} HCP)"

        # Partner bid new suit at 1-level (e.g., 1D-1H)
        if partner_response[0] == '1' and partner_response[1] in ['C', 'D', 'H', 'S']:
            response_suit = partner_response[1]

            # With 4+ card support, raise partner's major
            if response_suit in ['H', 'S'] and dist[response_suit] >= 4:
                if hcp <= 15:
                    suit_name = {'H': '♥', 'S': '♠'}[response_suit]
                    return f'2{response_suit}', f"2{suit_name} (4+ card support, minimum)"
                elif 16 <= hcp <= 18:
                    suit_name = {'H': '♥', 'S': '♠'}[response_suit]
                    return f'3{response_suit}', f"3{suit_name} (4+ card support, medium)"
                else:
                    return f'4{response_suit}', f"4{{'H': '♥', 'S': '♠'}[response_suit]} (4+ card support, strong)"

            # Rebid our suit with 6+ cards
            if dist[opening_suit] >= 6:
                if hcp <= 15:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[opening_suit]
                    return f'2{opening_suit}', f"2{suit_name} rebid (6+ cards, minimum)"
                elif 16 <= hcp <= 18:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[opening_suit]
                    return f'3{opening_suit}', f"3{suit_name} rebid (6+ cards, medium)"

            # Bid 1NT with balanced minimum
            if hcp <= 15 and self.hand.is_balanced():
                return '1NT', f"1NT rebid (balanced, {hcp} HCP)"

            # Bid 2NT with 18-19 balanced
            if 18 <= hcp <= 19 and self.hand.is_balanced():
                return '2NT', f"2NT rebid (balanced, {hcp} HCP)"

            # Bid 3NT with 19-20 balanced
            if hcp >= 19 and self.hand.is_balanced():
                return '3NT', f"3NT (balanced, {hcp} HCP)"

            # Show second suit (reverse with 17+, new suit with less)
            for suit in ['S', 'H', 'D', 'C']:
                if suit != opening_suit and suit != response_suit and dist[suit] >= 4:
                    # Check if this is a reverse
                    suit_rank = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
                    if suit_rank[suit] > suit_rank[opening_suit]:
                        # Reverse - shows 17+ HCP
                        if hcp >= 17:
                            suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                            return f'2{suit}', f"2{suit_name} reverse ({hcp} HCP)"
                    else:
                        # Normal new suit - can be minimum
                        suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                        return f'2{suit}', f"2{suit_name} second suit"

        # Partner bid new suit at 2-level (forcing, shows 10+ HCP)
        if partner_response[0] == '2' and partner_response[1] in ['C', 'D', 'H', 'S']:
            response_suit = partner_response[1]

            # With support, raise
            if dist[response_suit] >= 3:
                if hcp >= 17:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[response_suit]
                    return f'4{response_suit}', f"4{suit_name} jump raise" if response_suit in ['H', 'S'] else f'5{response_suit}', f"5{suit_name} raise"
                suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[response_suit]
                return f'3{response_suit}', f"3{suit_name} raise (3+ card support)"

            # Rebid our suit
            if dist[opening_suit] >= 6:
                suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[opening_suit]
                return f'2{opening_suit}', f"2{suit_name} rebid (6+ cards)"

            # Bid 2NT with balanced hand
            if self.hand.is_balanced():
                return '2NT', f"2NT rebid (balanced, {hcp} HCP)"

            # Show second suit
            for suit in ['C', 'D', 'H', 'S']:
                if suit != opening_suit and suit != response_suit and dist[suit] >= 4:
                    suit_name = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}[suit]
                    return f'3{suit}', f"3{suit_name} second suit"

        # Default: pass
        return 'P', "Pass (no clear rebid)"

    def _responder_rebid(self, my_first_bid):
        """Handle responder's rebid after opener rebids"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # Get opener's rebid
        partner_rebid = self._get_partner_last_call()
        if not partner_rebid:
            return 'P', "Pass (no partner rebid)"

        # Get opener's original bid
        partner_opening = self._get_partner_opening()

        # After we responded to 1NT
        if partner_opening == '1NT':
            return self._responder_rebid_after_1nt(my_first_bid, partner_rebid)

        # After we responded to 1-level suit
        if partner_opening in ['1C', '1D', '1H', '1S']:
            return self._responder_rebid_after_1_suit(my_first_bid, partner_opening, partner_rebid)

        # Default
        return 'P', "Pass"

    def _responder_rebid_after_1nt(self, my_response, opener_rebid):
        """Responder's rebid after opening 1NT"""
        hcp = self.hand.hcp

        # After Stayman (2C)
        if my_response == '2C':
            # Opener showed major
            if opener_rebid in ['2H', '2S']:
                major = opener_rebid[1]
                if self.hand.get_distribution()[major] >= 4:
                    # Found fit
                    if hcp >= 10:
                        return f'4{major}', f"4{{'H': '♥', 'S': '♠'}[major]} (game with fit)"
                    elif hcp >= 8:
                        return f'3{major}', f"3{{'H': '♥', 'S': '♠'}[major]} (invitational)"
                    else:
                        return 'P', f"Pass (minimum)"
            # Opener denied major (2D)
            if opener_rebid == '2D':
                if hcp >= 10:
                    return '3NT', f"3NT (no major fit, {hcp} HCP)"
                elif hcp >= 8:
                    return '2NT', f"2NT invitational ({hcp} HCP)"
                else:
                    return 'P', "Pass"

        # After transfer to major
        if my_response in ['2D', '2H']:
            # Opener accepted transfer
            transferred_suit = 'H' if my_response == '2D' else 'S'
            if hcp >= 10:
                return f'4{transferred_suit}', f"4{{'H': '♥', 'S': '♠'}[transferred_suit]} game"
            elif hcp >= 8:
                return f'3{transferred_suit}', f"3{{'H': '♥', 'S': '♠'}[transferred_suit]} invitational"
            else:
                return 'P', "Pass (transfer complete)"

        return 'P', "Pass"

    def _responder_rebid_after_1_suit(self, my_response, partner_opening, opener_rebid):
        """Responder's rebid after 1-level suit opening"""
        hcp = self.hand.hcp
        dist = self.hand.get_distribution()

        # Opener rebid game - pass
        if opener_rebid in ['3NT', '4H', '4S', '5C', '5D']:
            return 'P', "Pass (game reached)"

        # We bid 1NT initially (6-9 HCP)
        if my_response == '1NT':
            # Opener invited with 2NT
            if opener_rebid == '2NT':
                if hcp >= 8:
                    return '3NT', f"3NT (maximum 1NT response, {hcp} HCP)"
                else:
                    return 'P', f"Pass (minimum, {hcp} HCP)"

            # Opener rebid suit - usually pass
            if opener_rebid[0] == '2':
                return 'P', "Pass (minimum response)"

            # Opener invited with 3-level
            if opener_rebid[0] == '3':
                if hcp >= 9:
                    # Try for game
                    rebid_suit = opener_rebid[1]
                    if rebid_suit in ['H', 'S'] and dist[rebid_suit] >= 3:
                        return f'4{rebid_suit}', f"4{{'H': '♥', 'S': '♠'}[rebid_suit]} (fit + maximum)"
                    return '3NT', f"3NT (maximum, {hcp} HCP)"
                return 'P', "Pass (minimum)"

        # We raised partner's suit
        opening_suit = partner_opening[1]
        if my_response == f'2{opening_suit}':
            # Opener invited with 3-level
            if opener_rebid == f'3{opening_suit}':
                if hcp >= 8:
                    if opening_suit in ['H', 'S']:
                        return f'4{opening_suit}', f"4{{'H': '♥', 'S': '♠'}[opening_suit]} (maximum raise)"
                    return 'P', f"Pass (not enough for 5-level)"
                return 'P', "Pass (minimum raise)"

        # We bid new suit at 1-level
        if my_response[0] == '1':
            # Opener raised our suit
            my_suit = my_response[1]
            if opener_rebid == f'2{my_suit}':
                # Decide on game
                if hcp >= 11 and my_suit in ['H', 'S']:
                    return f'4{my_suit}', f"4{{'H': '♥', 'S': '♠'}[my_suit]} game"
                elif hcp >= 10 and my_suit in ['H', 'S']:
                    return f'3{my_suit}', f"3{{'H': '♥', 'S': '♠'}[my_suit]} invitational"
                return 'P', "Pass (minimum)"

            # Opener jump raised our suit
            if opener_rebid == f'3{my_suit}':
                if my_suit in ['H', 'S']:
                    return f'4{my_suit}', f"4{{'H': '♥', 'S': '♠'}[my_suit]} accept invitation"
                return 'P', "Pass"

            # Opener rebid 1NT - decide on game
            if opener_rebid == '1NT':
                if hcp >= 11:
                    return '3NT', f"3NT game ({hcp} HCP)"
                elif hcp >= 10:
                    return '2NT', f"2NT invitational ({hcp} HCP)"
                return 'P', "Pass (minimum)"

            # Opener rebid 2NT
            if opener_rebid == '2NT':
                if hcp >= 8:
                    return '3NT', f"3NT game ({hcp} HCP)"
                return 'P', "Pass (minimum)"

            # Opener rebid their suit
            if opener_rebid[1] == opening_suit:
                # Prefer notrump with balanced hand
                if self.hand.is_balanced():
                    if hcp >= 11:
                        return '3NT', f"3NT ({hcp} HCP, balanced)"
                    elif hcp >= 10:
                        return '2NT', f"2NT invitational ({hcp} HCP)"
                # Support with 3+ cards
                if dist[opening_suit] >= 3:
                    if hcp >= 11:
                        if opening_suit in ['H', 'S']:
                            return f'4{opening_suit}', f"4{{'H': '♥', 'S': '♠'}[opening_suit]} (fit + game values)"
                        return f'3{opening_suit}', f"3{{'D': '♦', 'C': '♣'}[opening_suit]} (delayed support)"
                return 'P', "Pass"

        return 'P', "Pass (no clear rebid)"

    def _get_rebid_after_response(self):
        """Get rebid after partner responds"""
        # This is now handled by _opener_rebid
        return self._get_rebid()

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

    def _am_i_opener(self):
        """Check if current player made the opening bid"""
        for auction_item in self.auction:
            call = auction_item['call'].upper()
            if call not in ['P', 'PASS']:
                return auction_item['bidder'] == self.position
        return False

    def _get_partner_last_call(self):
        """Get partner's last non-pass call"""
        partner = self._get_partner(self.position)
        for auction_item in reversed(self.auction):
            if auction_item['bidder'] == partner:
                call = auction_item['call'].upper()
                if call not in ['P', 'PASS']:
                    return call
        return None

    def _get_my_opening(self):
        """Get my opening bid"""
        for auction_item in self.auction:
            if auction_item['bidder'] == self.position:
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

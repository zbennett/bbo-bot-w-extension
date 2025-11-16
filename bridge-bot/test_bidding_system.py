"""
Comprehensive unit tests for Standard American bidding system
"""

import unittest
from bidding_system import StandardAmericanBidding, Hand


class TestHandEvaluation(unittest.TestCase):
    """Test hand evaluation methods"""

    def test_hcp_counting(self):
        """Test high card point counting"""
        # 15 HCP: AK in spades (7), AK in hearts (7), Q in diamonds (2) = 16
        hand = Hand('SAKSHAKDQC54321')
        self.assertEqual(hand.hcp, 16)

    def test_balanced_hand(self):
        """Test balanced hand detection"""
        # 4-3-3-3
        hand = Hand('SAKJ2HQ54DK32CJ98')
        self.assertTrue(hand.is_balanced())

        # 5-3-3-2
        hand = Hand('SAKQJ2HQ54DK32C98')
        self.assertTrue(hand.is_balanced())

        # 5-4-2-2 (not balanced)
        hand = Hand('SAKQJ2HQJ54DK3C98')
        self.assertFalse(hand.is_balanced())

    def test_semi_balanced_hand(self):
        """Test semi-balanced hand detection"""
        # 5-4-2-2
        hand = Hand('SAKQJ2HQJ54DK3C98')
        self.assertTrue(hand.is_semi_balanced())

        # 6-3-2-2
        hand = Hand('SAKQJ32HQ54DK3C98')
        self.assertTrue(hand.is_semi_balanced())

    def test_stopper_detection(self):
        """Test stopper detection in suits"""
        hand = Hand('SAHAKDQJ32CKQ54')
        self.assertTrue(hand.has_stopper('S'))  # Ace
        self.assertTrue(hand.has_stopper('H'))  # Ace
        self.assertTrue(hand.has_stopper('D'))  # QJx
        self.assertTrue(hand.has_stopper('C'))  # KQx


class TestOpeningBids(unittest.TestCase):
    """Test opening bid recommendations"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()

    def test_1nt_opening(self):
        """Test 1NT opening (15-17 HCP, balanced)"""
        # 16 HCP, 4-3-3-3
        self.bidding.set_hand('SAQ2HKJ4DKJ3CQ987')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1NT')
        self.assertIn('balanced', reasoning.lower())

    def test_2nt_opening(self):
        """Test 2NT opening (20-21 HCP, balanced)"""
        # 20 HCP, balanced 4-3-3-3
        self.bidding.set_hand('SAK98HAK9DQ32CKJ9')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2NT')

    def test_2c_strong_opening(self):
        """Test 2C strong opening (22+ HCP)"""
        # 23 HCP
        self.bidding.set_hand('SAKQJHAKQJDAK2CKQ')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2C')
        self.assertIn('22+', reasoning)

    def test_weak_2_opening(self):
        """Test weak 2-bid (6-card suit, 5-11 HCP)"""
        # 8 HCP, 6 spades
        self.bidding.set_hand('SKQJ987H54D432CA9')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2S')
        self.assertIn('Weak', reasoning)

    def test_1_major_opening(self):
        """Test 1-level major opening (5+ cards, 12+ HCP)"""
        # 13 HCP, 5 spades
        self.bidding.set_hand('SAKQJ2HK54D432C98')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1S')

    def test_1_minor_opening(self):
        """Test 1-level minor opening"""
        # 13 HCP, no 5-card major, 4 diamonds
        self.bidding.set_hand('SAK2HKJ4DKJ32CA98')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1D')

    def test_pass_insufficient_values(self):
        """Test passing with insufficient values"""
        # 10 HCP, not enough to open
        self.bidding.set_hand('SAJ2HK54DQ432CJ98')
        self.bidding.set_auction([], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, 'P')


class TestResponsesTo1NT(unittest.TestCase):
    """Test responses to 1NT opening"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()

    def test_stayman_with_major(self):
        """Test Stayman with 4-card major and game-going values"""
        # 10 HCP, 4 hearts
        self.bidding.set_hand('SAJ2HKQJ4D432CQ98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2C')
        self.assertIn('Stayman', reasoning)

    def test_transfer_to_hearts(self):
        """Test Jacoby transfer to hearts"""
        # 7 HCP, 6 hearts, no 4-card major (sign-off)
        self.bidding.set_hand('S32HKJ9654D432CQ9')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2D')
        self.assertIn('transfer', reasoning.lower())

    def test_3nt_game_balanced(self):
        """Test 3NT game bid with balanced hand"""
        # 11 HCP, balanced, no major
        self.bidding.set_hand('SAJ2HKJ4DKJ32CQ98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '3NT')

    def test_pass_weak_balanced(self):
        """Test passing 1NT with weak balanced hand"""
        # 5 HCP, balanced
        self.bidding.set_hand('SAJ2H654D432CJ987')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, 'P')


class TestResponsesTo1Suit(unittest.TestCase):
    """Test responses to 1-level suit openings"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()

    def test_simple_raise_major(self):
        """Test simple raise of partner's major"""
        # 8 HCP, 3-card support
        self.bidding.set_hand('SAJ2HKJ4D9654C987')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2H')

    def test_limit_raise(self):
        """Test limit raise (10-12 HCP, 4+ support)"""
        # 10 HCP, 4-card support
        self.bidding.set_hand('SA32HKQJ4D654CQ87')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '3H')
        self.assertIn('limit', reasoning.lower())

    def test_1nt_response(self):
        """Test 1NT response (6-10 HCP, no fit)"""
        # 7 HCP, no fit, no 4-card suit to bid, balanced
        self.bidding.set_hand('SA32HK4DQ32C98762')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1NT')

    def test_new_suit_1_level(self):
        """Test new suit at 1-level"""
        # 8 HCP, 4 spades
        self.bidding.set_hand('SKQJ2H54DQ54CJ987')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1D'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1S')

    def test_pass_insufficient(self):
        """Test passing with insufficient values"""
        # 4 HCP
        self.bidding.set_hand('S432H654DQ54CJ987')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, 'P')


class TestOpenerRebids(unittest.TestCase):
    """Test opener's rebid logic"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()

    def test_1nt_opener_stayman_response(self):
        """Test 1NT opener responding to Stayman"""
        # 16 HCP, 4 hearts
        self.bidding.set_hand('SAK2HKQJ4DQJ3CA98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2C'},
            {'bidder': 'W', 'call': 'P'}
        ], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2H')

    def test_1nt_opener_no_major(self):
        """Test 1NT opener denying major after Stayman"""
        # 16 HCP, no 4-card major
        self.bidding.set_hand('SAK2HKQ3DQJ32CA98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2C'},
            {'bidder': 'W', 'call': 'P'}
        ], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2D')

    def test_suit_opener_minimum_rebid(self):
        """Test minimum rebid after 1NT response"""
        # 13 HCP, 6 hearts
        self.bidding.set_hand('SA2HKQJ654D432CK9')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '1NT'},
            {'bidder': 'W', 'call': 'P'}
        ], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2H')

    def test_suit_opener_pass_1nt(self):
        """Test passing 1NT with minimum balanced"""
        # 13 HCP, balanced, 5 hearts
        self.bidding.set_hand('SAK2HKQJ42D432CJ9')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '1NT'},
            {'bidder': 'W', 'call': 'P'}
        ], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, 'P')

    def test_suit_opener_raise_partner(self):
        """Test raising partner's suit with support"""
        # 14 HCP, 4 spades
        self.bidding.set_hand('SAKQ2HKQ42D432CJ9')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '1S'},
            {'bidder': 'W', 'call': 'P'}
        ], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '2S')

    def test_suit_opener_game_after_limit_raise(self):
        """Test bidding game after limit raise"""
        # 17 HCP
        self.bidding.set_hand('SAKQ2HAKQ42D32CJ9')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '3H'},  # Limit raise
            {'bidder': 'W', 'call': 'P'}
        ], 'N')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '4H')


class TestResponderRebids(unittest.TestCase):
    """Test responder's rebid logic"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()

    def test_stayman_accept_major_fit(self):
        """Test accepting major fit after Stayman"""
        # 11 HCP, 4 hearts
        self.bidding.set_hand('SAJ2HKQJ4D432CQ98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2C'},
            {'bidder': 'W', 'call': 'P'},
            {'bidder': 'N', 'call': '2H'},  # Opener shows hearts
            {'bidder': 'E', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '4H')

    def test_transfer_complete_game(self):
        """Test completing transfer and bidding game"""
        # 11 HCP, 5 hearts
        self.bidding.set_hand('SAJ2HKQJ54D432CQ9')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2D'},  # Transfer
            {'bidder': 'W', 'call': 'P'},
            {'bidder': 'N', 'call': '2H'},  # Accept
            {'bidder': 'E', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '4H')

    def test_accept_invitation_maximum(self):
        """Test accepting game try with maximum"""
        # 9 HCP initially raised to 2H
        self.bidding.set_hand('SAJ2HKJ4D9654CQ98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2H'},
            {'bidder': 'W', 'call': 'P'},
            {'bidder': 'N', 'call': '3H'},  # Game try
            {'bidder': 'E', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '4H')

    def test_pass_game_reached(self):
        """Test passing when game is reached"""
        # Any hand
        self.bidding.set_hand('SAJ2HKJ4D9654CQ98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1H'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2H'},
            {'bidder': 'W', 'call': 'P'},
            {'bidder': 'N', 'call': '4H'},  # Game
            {'bidder': 'E', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, 'P')


class TestCompetitiveBidding(unittest.TestCase):
    """Test competitive bidding (overcalls, doubles)"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()

    def test_simple_overcall(self):
        """Test simple overcall (8-17 HCP, 5+ suit)"""
        # 12 HCP, 5 spades, 2+ quick tricks
        self.bidding.set_hand('SKQJ42HAK4D432C98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': 'P'},
            {'bidder': 'E', 'call': '1D'},
            {'bidder': 'S', 'call': 'P'},
            {'bidder': 'W', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1S')
        self.assertIn('overcall', reasoning.lower())

    def test_1nt_overcall(self):
        """Test 1NT overcall (15-18 HCP, balanced, stopper)"""
        # 16 HCP, balanced, diamond stopper
        self.bidding.set_hand('SAK2HKQ4DKJ3CQ987')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': 'P'},
            {'bidder': 'E', 'call': '1D'},
            {'bidder': 'S', 'call': 'P'},
            {'bidder': 'W', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, '1NT')
        self.assertIn('overcall', reasoning.lower())

    def test_takeout_double(self):
        """Test takeout double"""
        # 13 HCP, shortage in opponent's suit, support for unbid suits
        self.bidding.set_hand('SAKQ2HKJ42DQ2CJ98')
        self.bidding.set_auction([
            {'bidder': 'N', 'call': 'P'},
            {'bidder': 'E', 'call': '1D'},
            {'bidder': 'S', 'call': 'P'},
            {'bidder': 'W', 'call': 'P'}
        ], 'S')
        bid, reasoning = self.bidding.get_recommendation()
        self.assertEqual(bid, 'D')
        self.assertIn('takeout', reasoning.lower())


class TestAuctionHelpers(unittest.TestCase):
    """Test auction helper methods"""

    def setUp(self):
        self.bidding = StandardAmericanBidding()
        self.bidding.set_hand('SAK2HKJ4D432CQ987')

    def test_partner_identification(self):
        """Test identifying partner"""
        self.bidding.position = 'N'
        self.assertEqual(self.bidding._get_partner('N'), 'S')
        self.assertEqual(self.bidding._get_partner('E'), 'W')

    def test_lho_rho_identification(self):
        """Test LHO/RHO identification"""
        self.assertEqual(self.bidding._get_lho('N'), 'E')
        self.assertEqual(self.bidding._get_rho('N'), 'W')

    def test_am_i_opener(self):
        """Test checking if current player opened"""
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'}
        ], 'N')
        self.assertTrue(self.bidding._am_i_opener())

        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'}
        ], 'E')
        self.assertFalse(self.bidding._am_i_opener())

    def test_get_partner_opening(self):
        """Test getting partner's opening bid"""
        self.bidding.set_auction([
            {'bidder': 'N', 'call': '1NT'},
            {'bidder': 'E', 'call': 'P'},
            {'bidder': 'S', 'call': '2C'}
        ], 'S')
        self.assertEqual(self.bidding._get_partner_opening(), '1NT')


if __name__ == '__main__':
    unittest.main()

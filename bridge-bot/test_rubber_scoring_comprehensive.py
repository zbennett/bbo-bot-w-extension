"""
Comprehensive unit tests for rubber bridge scoring system.

Tests all scoring rules:
- Contract scoring (made, defeated, doubled, redoubled)
- Game completion and vulnerability
- Rubber bonuses (500 for 2-0, 700 for 2-1)
- Part score bonuses (50 at end of rubber)
- Slam bonuses
- Honor points
- No per-hand game bonuses (rubber bridge rule)
"""

import unittest
from rubber_scoring import RubberScoring


class TestBasicContractScoring(unittest.TestCase):
    """Test basic contract scoring without game bonuses"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_part_score_no_bonus(self):
        """Part scores should have NO bonus points during play"""
        # 1NT making exactly = 40 points below the line ONLY
        result = self.scorer.record_hand_result('1NT', 'N', 7)
        score = result['score']
        
        self.assertEqual(score['below_line'], 40)
        self.assertEqual(score['above_line'], 0)  # NO bonus
        self.assertEqual(score['total'], 40)
        self.assertFalse(score['makes_game'])
    
    def test_game_contract_no_bonus(self):
        """Game contracts should have NO bonus points during play"""
        # 3NT making exactly = 100 points below the line ONLY
        result = self.scorer.record_hand_result('3NT', 'N', 9)
        score = result['score']
        
        self.assertEqual(score['below_line'], 100)
        self.assertEqual(score['above_line'], 0)  # NO game bonus
        self.assertEqual(score['total'], 100)
        self.assertTrue(score['makes_game'])
    
    def test_major_suit_game(self):
        """4H/4S making = 120 below, no bonus"""
        result = self.scorer.record_hand_result('4S', 'S', 10)
        score = result['score']
        
        self.assertEqual(score['below_line'], 120)
        self.assertEqual(score['above_line'], 0)
        self.assertEqual(score['total'], 120)
    
    def test_minor_suit_game(self):
        """5C/5D making = 100 below, no bonus"""
        result = self.scorer.record_hand_result('5C', 'W', 11)
        score = result['score']
        
        self.assertEqual(score['below_line'], 100)
        self.assertEqual(score['above_line'], 0)
        self.assertEqual(score['total'], 100)


class TestOvertricks(unittest.TestCase):
    """Test overtrick scoring (above the line)"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_part_score_overtricks(self):
        """Overtricks in part scores go above the line"""
        # 1NT making 8 tricks (1 overtrick)
        result = self.scorer.record_hand_result('1NT', 'N', 8)
        score = result['score']
        
        self.assertEqual(score['below_line'], 40)
        self.assertEqual(score['above_line'], 30)  # 1 overtrick in NT
        self.assertEqual(score['total'], 70)
        self.assertEqual(score['overtricks'], 1)
    
    def test_game_contract_overtricks(self):
        """Overtricks in game contracts"""
        # 3NT making 10 tricks (1 overtrick)
        result = self.scorer.record_hand_result('3NT', 'N', 10)
        score = result['score']
        
        self.assertEqual(score['below_line'], 100)
        self.assertEqual(score['above_line'], 30)  # 1 overtrick
        self.assertEqual(score['total'], 130)
    
    def test_multiple_overtricks(self):
        """Multiple overtricks"""
        # 2S making 11 tricks (3 overtricks)
        result = self.scorer.record_hand_result('2S', 'E', 11)
        score = result['score']
        
        self.assertEqual(score['below_line'], 60)
        self.assertEqual(score['above_line'], 90)  # 3 × 30
        self.assertEqual(score['overtricks'], 3)


class TestDoubledContracts(unittest.TestCase):
    """Test doubled and redoubled contracts"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_doubled_made(self):
        """Doubled contract made"""
        # 1NT doubled making exactly
        result = self.scorer.record_hand_result('1NT', 'N', 7, doubled=True)
        score = result['score']
        
        self.assertEqual(score['below_line'], 80)  # 40 × 2
        self.assertEqual(score['above_line'], 50)  # Double bonus only
        self.assertEqual(score['total'], 130)
    
    def test_redoubled_made(self):
        """Redoubled contract made"""
        # 1NT redoubled making exactly
        result = self.scorer.record_hand_result('1NT', 'N', 7, redoubled=True)
        score = result['score']
        
        self.assertEqual(score['below_line'], 160)  # 40 × 4
        self.assertEqual(score['above_line'], 100)  # Redouble bonus
        self.assertEqual(score['total'], 260)
    
    def test_doubled_overtricks_not_vulnerable(self):
        """Doubled overtricks when not vulnerable"""
        # 1NT doubled, making 8 (1 overtrick), not vulnerable
        result = self.scorer.record_hand_result('1NT', 'N', 8, doubled=True)
        score = result['score']
        
        self.assertEqual(score['below_line'], 80)
        self.assertEqual(score['above_line'], 150)  # 50 (double) + 100 (overtrick)
    
    def test_doubled_overtricks_vulnerable(self):
        """Doubled overtricks when vulnerable"""
        # Make NS vulnerable first
        self.scorer.record_hand_result('3NT', 'N', 9)  # Win a game
        
        # Now 1NT doubled, making 8 (1 overtrick), vulnerable
        result = self.scorer.record_hand_result('1NT', 'S', 8, doubled=True)
        score = result['score']
        
        self.assertEqual(score['below_line'], 80)
        self.assertEqual(score['above_line'], 250)  # 50 (double) + 200 (overtrick vul)


class TestPenalties(unittest.TestCase):
    """Test penalty scoring for defeated contracts"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_undoubled_penalty_not_vulnerable(self):
        """Undoubled penalties when not vulnerable"""
        # 3NT down 2, not vulnerable
        result = self.scorer.record_hand_result('3NT', 'N', 7)  # Needs 9, made 7
        score = result['score']
        
        self.assertEqual(score['partnership'], 'EW')  # Defenders get points
        self.assertEqual(score['below_line'], 0)
        self.assertEqual(score['above_line'], 100)  # 2 × 50
        self.assertEqual(score['undertricks'], 2)
    
    def test_undoubled_penalty_vulnerable(self):
        """Undoubled penalties when vulnerable"""
        # Make NS vulnerable
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        # 3NT down 1, vulnerable
        result = self.scorer.record_hand_result('3NT', 'S', 8)
        score = result['score']
        
        self.assertEqual(score['partnership'], 'EW')
        self.assertEqual(score['above_line'], 100)  # 1 × 100 (vul)
    
    def test_doubled_penalty_not_vulnerable(self):
        """Doubled penalties when not vulnerable"""
        # 3NT doubled down 1, not vulnerable
        result = self.scorer.record_hand_result('3NT', 'N', 8, doubled=True)
        score = result['score']
        
        self.assertEqual(score['partnership'], 'EW')
        self.assertEqual(score['above_line'], 100)  # First undertrick
    
    def test_doubled_penalty_vulnerable(self):
        """Doubled penalties when vulnerable"""
        # Make NS vulnerable
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        # 3NT doubled down 2, vulnerable
        result = self.scorer.record_hand_result('3NT', 'S', 7, doubled=True)
        score = result['score']
        
        self.assertEqual(score['partnership'], 'EW')
        self.assertEqual(score['above_line'], 500)  # 200 + 300 (vul)


class TestSlams(unittest.TestCase):
    """Test slam bonuses"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_small_slam_not_vulnerable(self):
        """Small slam not vulnerable"""
        result = self.scorer.record_hand_result('6NT', 'N', 12)
        score = result['score']
        
        self.assertEqual(score['below_line'], 190)  # 40 + 5×30
        self.assertEqual(score['above_line'], 500)  # Small slam bonus
    
    def test_small_slam_vulnerable(self):
        """Small slam vulnerable"""
        # Make NS vulnerable
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        result = self.scorer.record_hand_result('6NT', 'S', 12)
        score = result['score']
        
        self.assertEqual(score['above_line'], 750)  # Small slam bonus (vul)
    
    def test_grand_slam_not_vulnerable(self):
        """Grand slam not vulnerable"""
        result = self.scorer.record_hand_result('7NT', 'N', 13)
        score = result['score']
        
        self.assertEqual(score['below_line'], 220)  # 40 + 6×30
        self.assertEqual(score['above_line'], 1000)  # Grand slam bonus
    
    def test_grand_slam_vulnerable(self):
        """Grand slam vulnerable"""
        # Make NS vulnerable
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        result = self.scorer.record_hand_result('7NT', 'S', 13)
        score = result['score']
        
        self.assertEqual(score['above_line'], 1500)  # Grand slam bonus (vul)


class TestGameProgression(unittest.TestCase):
    """Test game completion and vulnerability"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_game_completion(self):
        """Winning a game makes partnership vulnerable"""
        self.assertFalse(self.scorer.ns_vulnerable)
        
        # NS wins first game
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        self.assertEqual(self.scorer.ns_games, 1)
        self.assertTrue(self.scorer.ns_vulnerable)
        self.assertFalse(self.scorer.ew_vulnerable)
    
    def test_part_score_accumulation(self):
        """Part scores accumulate to make game"""
        # 2NT making = 70 below
        self.scorer.record_hand_result('2NT', 'N', 8)
        self.assertEqual(self.scorer.ns_below, 70)
        self.assertEqual(self.scorer.ns_games, 0)
        
        # 1NT making = 40 below (total 110 = game!)
        self.scorer.record_hand_result('1NT', 'S', 7)
        self.assertEqual(self.scorer.ns_games, 1)
        self.assertEqual(self.scorer.ns_below, 0)  # Reset after game
    
    def test_below_line_reset_on_game(self):
        """Below-the-line resets for BOTH sides when either wins game"""
        # EW gets 60 below
        self.scorer.record_hand_result('2S', 'E', 8)
        self.assertEqual(self.scorer.ew_below, 60)
        
        # NS wins game
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        # Both below lines reset
        self.assertEqual(self.scorer.ns_below, 0)
        self.assertEqual(self.scorer.ew_below, 0)


class TestRubberCompletion(unittest.TestCase):
    """Test rubber completion and bonuses"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_rubber_bonus_2_to_0(self):
        """Winning rubber 2-0 gives 500 bonus"""
        # NS wins first game
        self.scorer.record_hand_result('3NT', 'N', 9)
        self.assertFalse(self.scorer.rubber_complete)
        
        # NS wins second game (rubber complete!)
        result = self.scorer.record_hand_result('4S', 'S', 10)
        
        self.assertTrue(self.scorer.rubber_complete)
        self.assertEqual(self.scorer.ns_games, 2)
        self.assertEqual(self.scorer.ew_games, 0)
        
        # Check NS got 500 rubber bonus
        ns_total = self.scorer.ns_below + self.scorer.ns_above
        # 100 (3NT) + 120 (4S) + 500 (rubber) = 720
        self.assertEqual(ns_total, 720)
    
    def test_rubber_bonus_2_to_1(self):
        """Winning rubber 2-1 gives 700 bonus"""
        # NS wins first game
        self.scorer.record_hand_result('3NT', 'N', 9)
        
        # EW wins a game
        self.scorer.record_hand_result('4H', 'E', 10)
        
        # NS wins second game (rubber complete 2-1)
        self.scorer.record_hand_result('4S', 'S', 10)
        
        self.assertTrue(self.scorer.rubber_complete)
        self.assertEqual(self.scorer.ns_games, 2)
        self.assertEqual(self.scorer.ew_games, 1)
        
        # Check NS got 700 rubber bonus
        ns_total = self.scorer.ns_below + self.scorer.ns_above
        # 100 (3NT) + 120 (4S) + 700 (rubber) = 920
        self.assertEqual(ns_total, 920)
    
    def test_part_score_stays_on_scorecard(self):
        """Part scores stay on scorecard when opponent wins games"""
        # NS gets 60 below (part score)
        self.scorer.record_hand_result('2S', 'N', 8)
        self.assertEqual(self.scorer.ns_below, 60)
        
        # EW wins two games to complete rubber
        self.scorer.record_hand_result('3NT', 'E', 9)
        self.scorer.record_hand_result('4H', 'W', 10)
        
        # NS keeps their 60 points (moved to above when EW won first game)
        ns_total = self.scorer.ns_below + self.scorer.ns_above
        self.assertEqual(ns_total, 60)


class TestHonors(unittest.TestCase):
    """Test honor point calculation"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_four_trump_honors(self):
        """4 trump honors in one hand = 100 points"""
        hands = {
            'N': 'SAKQJH23D45C67',
            'E': 'S2H456D678C89T',
            'S': 'S3H789DTJQKCA',
            'W': 'S456789THJD2C'
        }
        
        result = self.scorer.record_hand_result('4S', 'N', 10, hands=hands)
        
        self.assertIn('honors', result['score'])
        honors = result['score']['honors']
        self.assertEqual(honors['partnership'], 'NS')
        self.assertEqual(honors['points'], 100)
        self.assertIn('4 trump honors', honors['description'])
    
    def test_five_trump_honors(self):
        """5 trump honors in one hand = 150 points"""
        hands = {
            'N': 'SAKQJTH2D45C67',
            'E': 'S2H3456D678C89',
            'S': 'S3H789DTJQKCA',
            'W': 'S456789HD2C'
        }
        
        result = self.scorer.record_hand_result('4S', 'N', 10, hands=hands)
        
        honors = result['score']['honors']
        self.assertEqual(honors['points'], 150)
        self.assertIn('5 trump honors', honors['description'])
    
    def test_four_aces_in_nt(self):
        """4 aces in NT = 150 points"""
        hands = {
            'N': 'SAHADA2CA',
            'E': 'S23H345D456C234',
            'S': 'S456H678D789C567',
            'W': 'S789TJQKHJD3C'
        }
        
        result = self.scorer.record_hand_result('3NT', 'N', 9, hands=hands)
        
        honors = result['score']['honors']
        self.assertEqual(honors['partnership'], 'NS')
        self.assertEqual(honors['points'], 150)
        self.assertIn('4 aces', honors['description'])
    
    def test_honors_to_opponents(self):
        """Honors go to partnership holding them, not declarer"""
        hands = {
            'N': 'S234H23D45C67',
            'E': 'SAKQJH456D678C89',  # EW has honors
            'S': 'S5H789DTJQKCA',
            'W': 'S6789TH2DC'
        }
        
        # NS declares and makes 4S, but EW holds honors
        result = self.scorer.record_hand_result('4S', 'N', 10, hands=hands)
        
        # NS gets 120 for making contract
        # Note: 4S is a game, so points move to above after game completes
        ns_total = self.scorer.ns_below + self.scorer.ns_above
        self.assertEqual(ns_total, 120)
        
        # EW gets 100 for honors
        self.assertEqual(self.scorer.ew_above, 100)
        honors = result['score']['honors']
        self.assertEqual(honors['partnership'], 'EW')


class TestComplexScenarios(unittest.TestCase):
    """Test complex multi-hand scenarios"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_complete_rubber_sequence(self):
        """Test a complete rubber with various hands"""
        # Hand 1: NS makes 1NT (part score)
        self.scorer.record_hand_result('1NT', 'N', 7)
        self.assertEqual(self.scorer.ns_below, 40)
        
        # Hand 2: EW makes 2S (part score)
        self.scorer.record_hand_result('2S', 'E', 8)
        self.assertEqual(self.scorer.ew_below, 60)
        
        # Hand 3: NS makes 3NT (game!) - both below lines reset
        self.scorer.record_hand_result('3NT', 'S', 9)
        self.assertEqual(self.scorer.ns_games, 1)
        self.assertEqual(self.scorer.ns_below, 0)
        self.assertEqual(self.scorer.ew_below, 0)  # Reset!
        
        # Hand 4: EW makes 4H (game)
        self.scorer.record_hand_result('4H', 'W', 10)
        self.assertEqual(self.scorer.ew_games, 1)
        
        # Hand 5: NS makes 4S (wins rubber 2-1)
        self.scorer.record_hand_result('4S', 'N', 10)
        self.assertTrue(self.scorer.rubber_complete)
        
        # Check final scores
        ns_total = self.scorer.ns_below + self.scorer.ns_above
        ew_total = self.scorer.ew_below + self.scorer.ew_above
        
        # NS: 40 (1NT) + 100 (3NT) + 120 (4S) + 700 (rubber) = 960
        self.assertEqual(ns_total, 960)
        
        # EW: 60 (2S) + 120 (4H) = 180
        self.assertEqual(ew_total, 180)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        self.scorer = RubberScoring()
    
    def test_exactly_100_points_makes_game(self):
        """100 points exactly is a game"""
        result = self.scorer.record_hand_result('5D', 'N', 11)  # Exactly 100
        self.assertTrue(result['score']['makes_game'])
        self.assertEqual(self.scorer.ns_games, 1)
    
    def test_99_points_not_game(self):
        """99 points is not a game"""
        result = self.scorer.record_hand_result('3D', 'N', 9)  # 60 points
        self.assertFalse(result['score']['makes_game'])
        self.assertEqual(self.scorer.ns_games, 0)
    
    def test_down_13_tricks(self):
        """Maximum penalty - down 13"""
        result = self.scorer.record_hand_result('7NT', 'N', 0, doubled=True)
        score = result['score']
        
        self.assertEqual(score['partnership'], 'EW')
        self.assertEqual(score['undertricks'], 13)
        self.assertGreater(score['above_line'], 3000)  # Huge penalty
    
    def test_new_rubber_after_completion(self):
        """Starting new rubber resets correctly"""
        # Complete a rubber
        self.scorer.record_hand_result('3NT', 'N', 9)
        self.scorer.record_hand_result('4S', 'S', 10)
        
        ns_rubbers = self.scorer.ns_rubbers
        self.assertEqual(ns_rubbers, 1)
        
        # Start new rubber
        self.scorer.start_new_rubber()
        
        # Check reset
        self.assertEqual(self.scorer.ns_games, 0)
        self.assertEqual(self.scorer.ew_games, 0)
        self.assertEqual(self.scorer.ns_below, 0)
        self.assertEqual(self.scorer.ew_below, 0)
        self.assertFalse(self.scorer.ns_vulnerable)
        self.assertFalse(self.scorer.ew_vulnerable)
        self.assertFalse(self.scorer.rubber_complete)
        
        # Rubber count preserved
        self.assertEqual(self.scorer.ns_rubbers, 1)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

"""
Rubber Bridge Scoring System
Implements complete rubber bridge scoring rules including:
- Game points (below the line)
- Premium points (above the line): overtricks, bonuses, penalties
- Vulnerability tracking
- Rubber bonuses (500 for 2-0, 700 for 2-1)
- Game progression (first to 2 games wins rubber)
"""


class RubberScoring:
    """
    Manages rubber bridge scoring for a session of hands.
    
    Rubber bridge rules:
    - First partnership to win 2 games wins the rubber
    - Game requires 100+ points below the line
    - Vulnerable after winning first game
    - Rubber bonus: 700 (2-1) or 500 (2-0)
    - All other points go above the line
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset for a new rubber"""
        # Score tracking
        self.ns_below = 0  # NS points below the line (towards game)
        self.ew_below = 0  # EW points below the line (towards game)
        self.ns_above = 0  # NS points above the line (bonuses, overtricks, etc.)
        self.ew_above = 0  # EW points above the line
        
        # Games won
        self.ns_games = 0
        self.ew_games = 0
        
        # Rubbers won (across multiple rubbers)
        self.ns_rubbers = 0
        self.ew_rubbers = 0
        
        # Vulnerability
        self.ns_vulnerable = False
        self.ew_vulnerable = False
        
        # History
        self.hand_history = []  # List of completed hands with scores
        self.rubber_history = []  # List of completed rubbers
        
        # Current rubber info
        self.current_rubber_number = 1
        self.rubber_complete = False
    
    def get_vulnerability(self, partnership):
        """Get vulnerability status for a partnership (NS or EW)"""
        if partnership in ['N', 'S', 'NS']:
            return self.ns_vulnerable
        else:
            return self.ew_vulnerable
    
    def calculate_contract_score(self, contract, declarer, tricks_made, doubled=False, redoubled=False):
        """
        Calculate score for a completed contract.
        
        Args:
            contract: Contract string (e.g., "3NT", "4H", "5Cx")
            declarer: Declarer position (N/E/S/W)
            tricks_made: Number of tricks actually made
            doubled: Whether contract was doubled
            redoubled: Whether contract was redoubled
            
        Returns:
            dict with scoring breakdown
        """
        # Parse contract
        level = int(contract[0])
        suit = contract[1:].replace('x', '').replace('X', '')
        
        partnership = 'NS' if declarer in ['N', 'S'] else 'EW'
        vulnerable = self.get_vulnerability(partnership)
        
        # Tricks needed
        tricks_needed = 6 + level
        
        # Check if made or defeated
        if tricks_made < tricks_needed:
            # Contract defeated
            return self._calculate_penalty(tricks_needed - tricks_made, vulnerable, doubled, redoubled, partnership)
        else:
            # Contract made
            overtricks = tricks_made - tricks_needed
            return self._calculate_made_contract(level, suit, overtricks, vulnerable, doubled, redoubled, partnership)
    
    def _calculate_made_contract(self, level, suit, overtricks, vulnerable, doubled, redoubled, partnership):
        """Calculate score for a made contract"""
        # Base trick values (per trick)
        trick_values = {
            'C': 20, 'D': 20,  # Minors
            'H': 30, 'S': 30,  # Majors
            'NT': 30  # First trick in NT is 40, rest are 30
        }
        
        # Calculate below-the-line (game) points
        if suit == 'NT':
            base_points = 40 + (level - 1) * 30  # First trick 40, rest 30
        else:
            base_points = level * trick_values[suit]
        
        if doubled:
            base_points *= 2
        if redoubled:
            base_points *= 4
        
        # Above-the-line points
        above_points = 0
        
        # Overtrick scoring
        if overtricks > 0:
            if doubled or redoubled:
                overtrick_value = 200 if vulnerable else 100
                if redoubled:
                    overtrick_value *= 2
                above_points += overtricks * overtrick_value
            else:
                if suit == 'NT':
                    above_points += overtricks * 30
                else:
                    above_points += overtricks * trick_values[suit]
        
        # Double/redouble bonus
        if doubled:
            above_points += 50
        if redoubled:
            above_points += 100
        
        # Slam bonuses
        if level == 6:  # Small slam
            above_points += 750 if vulnerable else 500
        elif level == 7:  # Grand slam
            above_points += 1500 if vulnerable else 1000
        
        # Check if contract makes game (100+ points)
        makes_game = base_points >= 100
        
        # Game bonus (only if not already vulnerable)
        if makes_game:
            above_points += 500 if vulnerable else 300
        else:
            # Part score bonus
            above_points += 50
        
        return {
            'partnership': partnership,
            'below_line': base_points,
            'above_line': above_points,
            'total': base_points + above_points,
            'makes_game': makes_game,
            'overtricks': overtricks,
            'vulnerable': vulnerable,
            'description': f"{level}{suit} made {'with ' + str(overtricks) + ' overtrick(s)' if overtricks > 0 else ''}"
        }
    
    def _calculate_penalty(self, undertricks, vulnerable, doubled, redoubled, declarer_partnership):
        """Calculate penalty for defeated contract"""
        # Determine defending partnership
        defender_partnership = 'EW' if declarer_partnership == 'NS' else 'NS'
        
        if not (doubled or redoubled):
            # Not doubled: 50 per trick not vulnerable, 100 vulnerable
            penalty = undertricks * (100 if vulnerable else 50)
        else:
            # Doubled/redoubled penalties are complex
            penalty = 0
            for i in range(undertricks):
                if i == 0:  # First undertrick
                    penalty += 200 if vulnerable else 100
                elif i in [1, 2]:  # 2nd and 3rd
                    penalty += 300 if vulnerable else 200
                else:  # 4th and beyond
                    penalty += 300
            
            if redoubled:
                penalty *= 2
        
        return {
            'partnership': defender_partnership,
            'below_line': 0,
            'above_line': penalty,
            'total': penalty,
            'makes_game': False,
            'undertricks': undertricks,
            'vulnerable': vulnerable,
            'description': f"Down {undertricks} ({'doubled' if doubled else 'redoubled' if redoubled else ''})"
        }
    
    def record_hand_result(self, contract, declarer, tricks_made, doubled=False, redoubled=False):
        """
        Record a completed hand and update rubber score.
        
        Returns:
            dict with hand result and current rubber status
        """
        # Calculate score
        score_result = self.calculate_contract_score(contract, declarer, tricks_made, doubled, redoubled)
        partnership = score_result['partnership']
        
        # Update scores
        if partnership == 'NS':
            self.ns_below += score_result['below_line']
            self.ns_above += score_result['above_line']
            
            # Check for game
            if score_result['makes_game'] or self.ns_below >= 100:
                self.ns_games += 1
                self.ns_vulnerable = True
                # Reset below-the-line for both sides
                self.ns_below = 0
                self.ew_below = 0
                score_result['game_won'] = True
        else:
            self.ew_below += score_result['below_line']
            self.ew_above += score_result['above_line']
            
            # Check for game
            if score_result['makes_game'] or self.ew_below >= 100:
                self.ew_games += 1
                self.ew_vulnerable = True
                # Reset below-the-line for both sides
                self.ns_below = 0
                self.ew_below = 0
                score_result['game_won'] = True
        
        # Check for rubber completion (first to 2 games)
        if self.ns_games >= 2 or self.ew_games >= 2:
            self._complete_rubber()
        
        # Add to history
        self.hand_history.append({
            'contract': contract,
            'declarer': declarer,
            'tricks_made': tricks_made,
            'score': score_result,
            'rubber_number': self.current_rubber_number
        })
        
        return {
            'score': score_result,
            'rubber_status': self.get_rubber_status()
        }
    
    def _complete_rubber(self):
        """Handle rubber completion and bonuses"""
        self.rubber_complete = True
        
        # Determine winner
        winner = 'NS' if self.ns_games >= 2 else 'EW'
        loser_games = self.ew_games if winner == 'NS' else self.ns_games
        
        # Rubber bonus
        rubber_bonus = 500 if loser_games == 0 else 700
        
        # Add bonus to winning partnership
        if winner == 'NS':
            self.ns_above += rubber_bonus
            self.ns_rubbers += 1
        else:
            self.ew_above += rubber_bonus
            self.ew_rubbers += 1
        
        # Record rubber
        self.rubber_history.append({
            'rubber_number': self.current_rubber_number,
            'winner': winner,
            'games': f"{self.ns_games}-{self.ew_games}",
            'ns_total': self.ns_below + self.ns_above,
            'ew_total': self.ew_below + self.ew_above,
            'bonus': rubber_bonus
        })
    
    def start_new_rubber(self):
        """Start a new rubber (keep lifetime stats)"""
        # Save rubber counts
        ns_rubbers = self.ns_rubbers
        ew_rubbers = self.ew_rubbers
        history = self.rubber_history.copy()
        
        # Reset
        self.reset()
        
        # Restore lifetime stats
        self.ns_rubbers = ns_rubbers
        self.ew_rubbers = ew_rubbers
        self.rubber_history = history
        self.current_rubber_number = len(history) + 1
    
    def get_rubber_status(self):
        """Get current rubber status"""
        ns_total = self.ns_below + self.ns_above
        ew_total = self.ew_below + self.ew_above
        
        # Get last hand info if available
        last_hand = None
        if self.hand_history:
            last = self.hand_history[-1]
            last_hand = {
                'contract': last['contract'],
                'declarer': last['declarer'],
                'tricks_made': last['tricks_made'],
                'score': last['score']
            }
        
        return {
            'rubber_number': self.current_rubber_number,
            'ns': {
                'below': self.ns_below,
                'above': self.ns_above,
                'total': ns_total,
                'games': self.ns_games,
                'vulnerable': self.ns_vulnerable,
                'rubbers': self.ns_rubbers
            },
            'ew': {
                'below': self.ew_below,
                'above': self.ew_above,
                'total': ew_total,
                'games': self.ew_games,
                'vulnerable': self.ew_vulnerable,
                'rubbers': self.ew_rubbers
            },
            'rubber_complete': self.rubber_complete,
            'hand_count': len(self.hand_history),
            'last_hand': last_hand
        }
    
    def get_score_summary(self):
        """Get formatted score summary"""
        status = self.get_rubber_status()
        
        return {
            'current_rubber': status,
            'rubber_history': self.rubber_history,
            'hand_history': self.hand_history[-5:] if len(self.hand_history) > 5 else self.hand_history  # Last 5 hands
        }

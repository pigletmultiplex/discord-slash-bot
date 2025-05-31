"""
Achievement system for tracking player accomplishments
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Achievement:
    def __init__(self, id: str, name: str, description: str, icon: str, 
                 requirement_type: str, requirement_value: int, xp_reward: int = 100):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.requirement_type = requirement_type
        self.requirement_value = requirement_value
        self.xp_reward = xp_reward

class AchievementManager:
    def __init__(self):
        self.achievements = self._initialize_achievements()
    
    def _initialize_achievements(self) -> Dict[str, Achievement]:
        """Initialize all available achievements"""
        achievements = {}
        
        # Balance achievements
        achievements['rich_1'] = Achievement(
            'rich_1', 'Getting Started', 'Reach 5,000 coins', '💰', 
            'balance', 5000, 100
        )
        achievements['rich_2'] = Achievement(
            'rich_2', 'Wealthy', 'Reach 50,000 coins', '💸', 
            'balance', 50000, 200
        )
        achievements['rich_3'] = Achievement(
            'rich_3', 'Millionaire', 'Reach 1,000,000 coins', '🏆', 
            'balance', 1000000, 500
        )
        
        # Games played achievements
        achievements['gamer_1'] = Achievement(
            'gamer_1', 'Novice Gambler', 'Play 10 games', '🎮', 
            'games_played', 10, 50
        )
        achievements['gamer_2'] = Achievement(
            'gamer_2', 'Experienced Player', 'Play 100 games', '🎯', 
            'games_played', 100, 150
        )
        achievements['gamer_3'] = Achievement(
            'gamer_3', 'Casino Veteran', 'Play 1,000 games', '🎰', 
            'games_played', 1000, 300
        )
        
        # Winning streak achievements
        achievements['winner_1'] = Achievement(
            'winner_1', 'Lucky Streak', 'Win 5 games in a row', '🍀', 
            'win_streak', 5, 100
        )
        achievements['winner_2'] = Achievement(
            'winner_2', 'Hot Streak', 'Win 10 games in a row', '🔥', 
            'win_streak', 10, 200
        )
        achievements['winner_3'] = Achievement(
            'winner_3', 'Unstoppable', 'Win 20 games in a row', '⚡', 
            'win_streak', 20, 400
        )
        
        # Big win achievements
        achievements['bigwin_1'] = Achievement(
            'bigwin_1', 'Nice Win', 'Win 10,000 coins in one game', '💵', 
            'single_win', 10000, 75
        )
        achievements['bigwin_2'] = Achievement(
            'bigwin_2', 'Jackpot', 'Win 100,000 coins in one game', '💎', 
            'single_win', 100000, 250
        )
        achievements['bigwin_3'] = Achievement(
            'bigwin_3', 'Mega Jackpot', 'Win 1,000,000 coins in one game', '👑', 
            'single_win', 1000000, 1000
        )
        
        # Total winnings achievements
        achievements['total_win_1'] = Achievement(
            'total_win_1', 'Profit Maker', 'Win 100,000 total coins', '📈', 
            'total_winnings', 100000, 100
        )
        achievements['total_win_2'] = Achievement(
            'total_win_2', 'High Roller', 'Win 1,000,000 total coins', '🎲', 
            'total_winnings', 1000000, 300
        )
        achievements['total_win_3'] = Achievement(
            'total_win_3', 'Casino Legend', 'Win 10,000,000 total coins', '🌟', 
            'total_winnings', 10000000, 750
        )
        
        # Game-specific achievements
        achievements['poker_master'] = Achievement(
            'poker_master', 'Poker Face', 'Win 50 poker games', '🃏', 
            'poker_wins', 50, 200
        )
        achievements['slots_king'] = Achievement(
            'slots_king', 'Slot Machine King', 'Win 100 slots games', '🎰', 
            'slots_wins', 100, 150
        )
        achievements['blackjack_ace'] = Achievement(
            'blackjack_ace', 'Blackjack Ace', 'Get 25 blackjacks', '🖤', 
            'blackjacks', 25, 180
        )
        
        # Risk taker achievements
        achievements['risk_1'] = Achievement(
            'risk_1', 'Risk Taker', 'Bet all-in 10 times', '⚠️', 
            'all_ins', 10, 120
        )
        achievements['risk_2'] = Achievement(
            'risk_2', 'Daredevil', 'Bet all-in 50 times', '💀', 
            'all_ins', 50, 300
        )
        
        # Social achievements
        achievements['daily_1'] = Achievement(
            'daily_1', 'Daily Player', 'Play games for 7 consecutive days', '📅', 
            'daily_streak', 7, 150
        )
        achievements['daily_2'] = Achievement(
            'daily_2', 'Dedicated Gambler', 'Play games for 30 consecutive days', '🗓️', 
            'daily_streak', 30, 500
        )
        
        return achievements
    
    def check_achievements(self, user_data: Dict[str, Any], 
                         game_result: Optional[Dict[str, Any]] = None) -> List[Achievement]:
        """Check if user has earned any new achievements"""
        newly_earned = []
        user_achievements = user_data.get('achievements', [])
        
        for achievement_id, achievement in self.achievements.items():
            if achievement_id in user_achievements:
                continue  # Already earned
            
            if self._check_achievement_requirement(achievement, user_data, game_result):
                newly_earned.append(achievement)
                user_achievements.append(achievement_id)
        
        # Update user data
        user_data['achievements'] = user_achievements
        return newly_earned
    
    def _check_achievement_requirement(self, achievement: Achievement, 
                                     user_data: Dict[str, Any], 
                                     game_result: Optional[Dict[str, Any]] = None) -> bool:
        """Check if achievement requirement is met"""
        req_type = achievement.requirement_type
        req_value = achievement.requirement_value
        
        if req_type == 'balance':
            return user_data.get('balance', 0) >= req_value
        elif req_type == 'games_played':
            return user_data.get('games_played', 0) >= req_value
        elif req_type == 'total_winnings':
            return user_data.get('total_winnings', 0) >= req_value
        elif req_type == 'win_streak':
            return user_data.get('current_win_streak', 0) >= req_value
        elif req_type == 'single_win':
            if game_result and game_result.get('won'):
                return game_result.get('winnings', 0) >= req_value
            return False
        elif req_type == 'poker_wins':
            return user_data.get('poker_wins', 0) >= req_value
        elif req_type == 'slots_wins':
            return user_data.get('slots_wins', 0) >= req_value
        elif req_type == 'blackjacks':
            return user_data.get('blackjacks', 0) >= req_value
        elif req_type == 'all_ins':
            return user_data.get('all_ins', 0) >= req_value
        elif req_type == 'daily_streak':
            return user_data.get('daily_streak', 0) >= req_value
        
        return False
    
    def get_user_achievements(self, user_data: Dict[str, Any]) -> List[Achievement]:
        """Get all achievements earned by user"""
        user_achievement_ids = user_data.get('achievements', [])
        return [self.achievements[aid] for aid in user_achievement_ids if aid in self.achievements]
    
    def get_achievement_progress(self, user_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get progress towards all achievements"""
        progress = {}
        user_achievements = user_data.get('achievements', [])
        
        for achievement_id, achievement in self.achievements.items():
            if achievement_id in user_achievements:
                progress[achievement_id] = {
                    'completed': True,
                    'current': achievement.requirement_value,
                    'target': achievement.requirement_value,
                    'percentage': 100
                }
            else:
                current = self._get_current_progress(achievement, user_data)
                percentage = min(100, (current / achievement.requirement_value) * 100)
                progress[achievement_id] = {
                    'completed': False,
                    'current': current,
                    'target': achievement.requirement_value,
                    'percentage': percentage
                }
        
        return progress
    
    def _get_current_progress(self, achievement: Achievement, user_data: Dict[str, Any]) -> int:
        """Get current progress value for an achievement"""
        req_type = achievement.requirement_type
        
        if req_type == 'balance':
            return user_data.get('balance', 0)
        elif req_type == 'games_played':
            return user_data.get('games_played', 0)
        elif req_type == 'total_winnings':
            return user_data.get('total_winnings', 0)
        elif req_type == 'win_streak':
            return user_data.get('current_win_streak', 0)
        elif req_type == 'single_win':
            return user_data.get('biggest_win', 0)
        elif req_type == 'poker_wins':
            return user_data.get('poker_wins', 0)
        elif req_type == 'slots_wins':
            return user_data.get('slots_wins', 0)
        elif req_type == 'blackjacks':
            return user_data.get('blackjacks', 0)
        elif req_type == 'all_ins':
            return user_data.get('all_ins', 0)
        elif req_type == 'daily_streak':
            return user_data.get('daily_streak', 0)
        
        return 0
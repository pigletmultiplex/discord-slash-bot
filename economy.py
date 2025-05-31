"""
Economy system for managing user balances, XP, and statistics
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EconomyManager:
    def __init__(self, data_file: str = "data/users.json"):
        self.data_file = data_file
        self.users_data = self._load_data()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(data_file), exist_ok=True)

    def _load_data(self) -> Dict[str, Any]:
        """Load user data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
        
        return {}

    def _save_data(self):
        """Save user data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.users_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user data: {e}")

    def _create_user(self, user_id: str) -> Dict[str, Any]:
        """Create a new user with default values"""
        now = datetime.now().isoformat()
        user_data = {
            "balance": 1000,  # Starting balance
            "xp": 0,
            "games_played": 0,
            "games_won": 0,
            "total_winnings": 0,
            "total_losses": 0,
            "created_at": now,
            "last_daily": None,
            "last_active": now,
            "achievements": [],
            "current_win_streak": 0,
            "biggest_win": 0,
            "poker_wins": 0,
            "slots_wins": 0,
            "blackjacks": 0,
            "all_ins": 0,
            "daily_streak": 0
        }
        
        self.users_data[user_id] = user_data
        self._save_data()
        return user_data

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data, creating if doesn't exist"""
        if user_id not in self.users_data:
            return self._create_user(user_id)
        
        # Update last active
        self.users_data[user_id]["last_active"] = datetime.now().isoformat()
        return self.users_data[user_id]

    def get_balance(self, user_id: str) -> int:
        """Get user's current balance"""
        user_data = self.get_user_data(user_id)
        return user_data["balance"]

    def add_balance(self, user_id: str, amount: int) -> int:
        """Add to user's balance"""
        user_data = self.get_user_data(user_id)
        user_data["balance"] += amount
        user_data["total_winnings"] += amount
        self._save_data()
        return user_data["balance"]

    def subtract_balance(self, user_id: str, amount: int) -> int:
        """Subtract from user's balance"""
        user_data = self.get_user_data(user_id)
        user_data["balance"] = max(0, user_data["balance"] - amount)
        user_data["total_losses"] += amount
        self._save_data()
        return user_data["balance"]

    def set_balance(self, user_id: str, amount: int) -> int:
        """Set user's balance to specific amount"""
        user_data = self.get_user_data(user_id)
        user_data["balance"] = max(0, amount)
        self._save_data()
        return user_data["balance"]

    def get_xp(self, user_id: str) -> int:
        """Get user's XP"""
        user_data = self.get_user_data(user_id)
        return user_data["xp"]

    def add_xp(self, user_id: str, amount: int) -> int:
        """Add XP to user"""
        user_data = self.get_user_data(user_id)
        user_data["xp"] += amount
        self._save_data()
        return user_data["xp"]

    def record_game(self, user_id: str, won: bool, winnings: int = 0, game_type: str = "general"):
        """Record game statistics"""
        user_data = self.get_user_data(user_id)
        user_data["games_played"] += 1
        
        if won:
            user_data["games_won"] += 1
            user_data["total_winnings"] += winnings
            user_data["current_win_streak"] = user_data.get("current_win_streak", 0) + 1
            
            # Update biggest win
            if winnings > user_data.get("biggest_win", 0):
                user_data["biggest_win"] = winnings
            
            # Game-specific win tracking
            if game_type == "poker":
                user_data["poker_wins"] = user_data.get("poker_wins", 0) + 1
            elif game_type == "slots":
                user_data["slots_wins"] = user_data.get("slots_wins", 0) + 1
        else:
            user_data["total_losses"] += abs(winnings)  # winnings will be negative for losses
            user_data["current_win_streak"] = 0  # Reset win streak
        
        # Track special events
        if game_type == "blackjack" and won and winnings > 0:
            user_data["blackjacks"] = user_data.get("blackjacks", 0) + 1
        
        # Update last active
        user_data["last_active"] = datetime.now().isoformat()
        
        self._save_data()
        
        # Return game result for achievement checking
        return {
            "won": won,
            "winnings": winnings,
            "game_type": game_type,
            "user_data": user_data
        }

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        user_data = self.get_user_data(user_id)
        
        games_played = user_data["games_played"]
        games_won = user_data["games_won"]
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        
        return {
            "balance": user_data["balance"],
            "xp": user_data["xp"],
            "games_played": games_played,
            "games_won": games_won,
            "win_rate": win_rate,
            "total_winnings": user_data["total_winnings"],
            "total_losses": user_data["total_losses"],
            "net_profit": user_data["total_winnings"] - user_data["total_losses"]
        }

    def claim_daily_bonus(self, user_id: str) -> Dict[str, Any]:
        """Claim daily bonus if available"""
        user_data = self.get_user_data(user_id)
        now = datetime.now()
        
        # Check if daily bonus is available
        last_daily = user_data.get("last_daily")
        if last_daily:
            last_daily_date = datetime.fromisoformat(last_daily)
            if now - last_daily_date < timedelta(days=1):
                remaining = timedelta(days=1) - (now - last_daily_date)
                return {
                    "success": False,
                    "message": f"Daily bonus available in {remaining}",
                    "amount": 0
                }
        
        # Give daily bonus
        bonus_amount = 500
        user_data["balance"] += bonus_amount
        user_data["last_daily"] = now.isoformat()
        self._save_data()
        
        return {
            "success": True,
            "message": "Daily bonus claimed!",
            "amount": bonus_amount
        }

    def get_leaderboard(self, limit: int = 10) -> list:
        """Get top users by balance"""
        users = []
        for user_id, data in self.users_data.items():
            users.append({
                "user_id": user_id,
                "balance": data["balance"],
                "xp": data["xp"],
                "games_played": data["games_played"],
                "games_won": data["games_won"]
            })
        
        # Sort by balance
        users.sort(key=lambda x: x["balance"], reverse=True)
        return users[:limit]

    def reset_user_data(self, user_id: str):
        """Reset user data to defaults"""
        if user_id in self.users_data:
            del self.users_data[user_id]
            self._save_data()
        
        # Create new user data
        self._create_user(user_id)

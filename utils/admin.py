"""
Admin panel utilities for bot management and user moderation
"""
import discord
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdminManager:
    def __init__(self, economy_manager, achievement_manager):
        self.economy = economy_manager
        self.achievements = achievement_manager
        
        # Admin user IDs - these should be set via configuration
        self.admin_users = set()
        
        # Bot statistics
        self.bot_stats = {
            "start_time": datetime.now(),
            "commands_executed": 0,
            "games_played": 0,
            "total_bets": 0,
            "total_winnings": 0
        }
    
    def add_admin(self, user_id: str):
        """Add a user as admin"""
        self.admin_users.add(user_id)
    
    def remove_admin(self, user_id: str):
        """Remove admin privileges from a user"""
        self.admin_users.discard(user_id)
    
    def is_admin(self, user_id: str) -> bool:
        """Check if user has admin privileges"""
        return user_id in self.admin_users
    
    def get_bot_statistics(self) -> Dict[str, Any]:
        """Get comprehensive bot statistics"""
        uptime = datetime.now() - self.bot_stats["start_time"]
        
        # Get user statistics
        all_users = self.economy.users_data
        total_users = len(all_users)
        active_users = len([u for u in all_users.values() 
                          if u.get('games_played', 0) > 0])
        
        total_balance = sum(u.get('balance', 0) for u in all_users.values())
        total_games = sum(u.get('games_played', 0) for u in all_users.values())
        total_winnings = sum(u.get('total_winnings', 0) for u in all_users.values())
        total_losses = sum(u.get('total_losses', 0) for u in all_users.values())
        
        # Top players
        top_balance = sorted(all_users.items(), 
                           key=lambda x: x[1].get('balance', 0), 
                           reverse=True)[:5]
        
        top_games = sorted(all_users.items(), 
                         key=lambda x: x[1].get('games_played', 0), 
                         reverse=True)[:5]
        
        return {
            "uptime": str(uptime).split('.')[0],
            "total_users": total_users,
            "active_users": active_users,
            "total_balance": total_balance,
            "total_games": total_games,
            "total_winnings": total_winnings,
            "total_losses": total_losses,
            "net_flow": total_winnings - total_losses,
            "top_balance": top_balance,
            "top_games": top_games,
            "commands_executed": self.bot_stats["commands_executed"]
        }
    
    def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        user_data = self.economy.get_user_data(user_id)
        user_achievements = self.achievements.get_user_achievements(user_data)
        progress = self.achievements.get_achievement_progress(user_data)
        
        return {
            "user_data": user_data,
            "achievements": user_achievements,
            "progress": progress,
            "achievement_count": len(user_achievements),
            "total_achievements": len(self.achievements.achievements)
        }
    
    def modify_user_balance(self, user_id: str, amount: int, reason: str = "Admin adjustment") -> Dict[str, Any]:
        """Modify a user's balance with logging"""
        old_balance = self.economy.get_balance(user_id)
        
        if amount > 0:
            new_balance = self.economy.add_balance(user_id, amount)
        else:
            new_balance = self.economy.subtract_balance(user_id, abs(amount))
        
        # Log the change
        change_log = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "change": amount,
            "reason": reason
        }
        
        logger.info(f"Admin balance change: {change_log}")
        
        return change_log
    
    def reset_user_data(self, user_id: str, reason: str = "Admin reset") -> bool:
        """Reset a user's data completely"""
        try:
            self.economy.reset_user_data(user_id)
            
            # Log the reset
            logger.info(f"Admin reset user {user_id}: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset user {user_id}: {e}")
            return False
    
    def ban_user(self, user_id: str, reason: str = "Banned by admin") -> bool:
        """Ban a user from using the bot"""
        try:
            user_data = self.economy.get_user_data(user_id)
            user_data["banned"] = True
            user_data["ban_reason"] = reason
            user_data["ban_timestamp"] = datetime.now().isoformat()
            
            self.economy._save_data()
            logger.info(f"Admin banned user {user_id}: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to ban user {user_id}: {e}")
            return False
    
    def unban_user(self, user_id: str) -> bool:
        """Unban a user"""
        try:
            user_data = self.economy.get_user_data(user_id)
            user_data["banned"] = False
            user_data.pop("ban_reason", None)
            user_data.pop("ban_timestamp", None)
            
            self.economy._save_data()
            logger.info(f"Admin unbanned user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unban user {user_id}: {e}")
            return False
    
    def is_user_banned(self, user_id: str) -> bool:
        """Check if a user is banned"""
        user_data = self.economy.get_user_data(user_id)
        return user_data.get("banned", False)
    
    def get_banned_users(self) -> List[Dict[str, Any]]:
        """Get list of all banned users"""
        banned = []
        for user_id, user_data in self.economy.users_data.items():
            if user_data.get("banned", False):
                banned.append({
                    "user_id": user_id,
                    "reason": user_data.get("ban_reason", "No reason"),
                    "timestamp": user_data.get("ban_timestamp", "Unknown")
                })
        return banned
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Check file system
            data_file_exists = self.economy.data_file and \
                             __import__('os').path.exists(self.economy.data_file)
            
            # Check data integrity
            users_count = len(self.economy.users_data)
            
            # Memory usage (basic check)
            import sys
            memory_usage = sys.getsizeof(self.economy.users_data)
            
            return {
                "status": "healthy",
                "data_file_exists": data_file_exists,
                "users_count": users_count,
                "memory_usage_bytes": memory_usage,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def backup_data(self) -> Dict[str, Any]:
        """Create a backup of user data"""
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "users_data": self.economy.users_data.copy(),
                "bot_stats": self.bot_stats.copy()
            }
            
            # Save backup to file
            import json
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(f"data/{backup_filename}", 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return {
                "success": True,
                "filename": backup_filename,
                "users_backed_up": len(backup_data["users_data"]),
                "timestamp": backup_data["timestamp"]
            }
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def increment_command_counter(self):
        """Increment the command execution counter"""
        self.bot_stats["commands_executed"] += 1
    
    def increment_game_counter(self):
        """Increment the games played counter"""
        self.bot_stats["games_played"] += 1
    
    def add_bet_amount(self, amount: int):
        """Add to total bet amount"""
        self.bot_stats["total_bets"] += amount
    
    def add_winnings_amount(self, amount: int):
        """Add to total winnings amount"""
        self.bot_stats["total_winnings"] += amount
    
    def create_admin_embed(self, title: str, data: Dict[str, Any]) -> discord.Embed:
        """Create a formatted embed for admin information"""
        embed = discord.Embed(
            title=f"🛠️ Admin Panel - {title}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                continue  # Skip complex data types for basic embed
            embed.add_field(
                name=key.replace('_', ' ').title(),
                value=str(value),
                inline=True
            )
        
        embed.set_footer(text="Admin Panel | Authorized Access Only")
        return embed
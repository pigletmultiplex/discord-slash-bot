"""
Cooldown management system
"""
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CooldownManager:
    def __init__(self):
        # Store cooldowns as {user_id: {command: expiry_timestamp}}
        self.cooldowns: Dict[str, Dict[str, float]] = {}
    
    def set_cooldown(self, user_id: str, command: str, duration: int):
        """Set a cooldown for a user and command"""
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}
        
        expiry_time = time.time() + duration
        self.cooldowns[user_id][command] = expiry_time
        
        logger.debug(f"Set cooldown for {user_id} on {command} for {duration}s")
    
    def is_on_cooldown(self, user_id: str, command: str) -> bool:
        """Check if a user is on cooldown for a command"""
        if user_id not in self.cooldowns:
            return False
        
        if command not in self.cooldowns[user_id]:
            return False
        
        current_time = time.time()
        expiry_time = self.cooldowns[user_id][command]
        
        if current_time >= expiry_time:
            # Cooldown expired, remove it
            del self.cooldowns[user_id][command]
            if not self.cooldowns[user_id]:  # Remove user entry if empty
                del self.cooldowns[user_id]
            return False
        
        return True
    
    def get_remaining_cooldown(self, user_id: str, command: str) -> float:
        """Get remaining cooldown time in seconds"""
        if not self.is_on_cooldown(user_id, command):
            return 0.0
        
        current_time = time.time()
        expiry_time = self.cooldowns[user_id][command]
        return max(0.0, expiry_time - current_time)
    
    def remove_cooldown(self, user_id: str, command: str):
        """Manually remove a cooldown"""
        if user_id in self.cooldowns and command in self.cooldowns[user_id]:
            del self.cooldowns[user_id][command]
            if not self.cooldowns[user_id]:
                del self.cooldowns[user_id]
            
            logger.debug(f"Removed cooldown for {user_id} on {command}")
    
    def get_user_cooldowns(self, user_id: str) -> Dict[str, float]:
        """Get all active cooldowns for a user"""
        if user_id not in self.cooldowns:
            return {}
        
        current_time = time.time()
        active_cooldowns = {}
        expired_commands = []
        
        for command, expiry_time in self.cooldowns[user_id].items():
            if current_time >= expiry_time:
                expired_commands.append(command)
            else:
                remaining = expiry_time - current_time
                active_cooldowns[command] = remaining
        
        # Clean up expired cooldowns
        for command in expired_commands:
            del self.cooldowns[user_id][command]
        
        if not self.cooldowns[user_id]:
            del self.cooldowns[user_id]
        
        return active_cooldowns
    
    def clear_user_cooldowns(self, user_id: str):
        """Clear all cooldowns for a user"""
        if user_id in self.cooldowns:
            del self.cooldowns[user_id]
            logger.debug(f"Cleared all cooldowns for {user_id}")
    
    def cleanup_expired(self):
        """Clean up all expired cooldowns"""
        current_time = time.time()
        users_to_remove = []
        
        for user_id, user_cooldowns in self.cooldowns.items():
            expired_commands = []
            
            for command, expiry_time in user_cooldowns.items():
                if current_time >= expiry_time:
                    expired_commands.append(command)
            
            # Remove expired commands
            for command in expired_commands:
                del user_cooldowns[command]
            
            # Mark user for removal if no cooldowns left
            if not user_cooldowns:
                users_to_remove.append(user_id)
        
        # Remove users with no cooldowns
        for user_id in users_to_remove:
            del self.cooldowns[user_id]
        
        logger.debug(f"Cleaned up expired cooldowns for {len(users_to_remove)} users")
    
    def get_cooldown_info(self, user_id: str, command: str) -> Dict[str, any]:
        """Get detailed cooldown information"""
        if not self.is_on_cooldown(user_id, command):
            return {
                "active": False,
                "remaining": 0.0,
                "expires_at": None
            }
        
        remaining = self.get_remaining_cooldown(user_id, command)
        expiry_time = self.cooldowns[user_id][command]
        expires_at = datetime.fromtimestamp(expiry_time)
        
        return {
            "active": True,
            "remaining": remaining,
            "expires_at": expires_at,
            "expires_at_str": expires_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def format_remaining_time(self, seconds: float) -> str:
        """Format remaining time in a readable format"""
        if seconds <= 0:
            return "Ready"
        
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            return f"{hours}h {remaining_minutes}m"

"""
Input validation utilities
"""
import re
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def validate_bet(bet_amount: int, user_balance: int, min_bet: int = 1, max_bet: Optional[int] = None) -> bool:
    """
    Validate if a bet amount is valid
    
    Args:
        bet_amount: The amount to bet
        user_balance: User's current balance
        min_bet: Minimum bet allowed
        max_bet: Maximum bet allowed (None for no limit)
    
    Returns:
        True if bet is valid, False otherwise
    """
    try:
        # Check if bet amount is positive
        if bet_amount <= 0:
            return False
        
        # Check minimum bet
        if bet_amount < min_bet:
            return False
        
        # Check maximum bet
        if max_bet is not None and bet_amount > max_bet:
            return False
        
        # Check if user has enough balance
        if bet_amount > user_balance:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Bet validation error: {e}")
        return False

def parse_bet_amount(bet_string: str, user_balance: int) -> int:
    """
    Parse bet amount from string input
    
    Args:
        bet_string: The bet input string (e.g., "100", "1k", "m", "a")
        user_balance: User's current balance
    
    Returns:
        Parsed bet amount as integer, or 0 if invalid
    """
    try:
        bet_string = bet_string.lower().strip()
        
        # Handle special cases
        if bet_string in ['m', 'max']:
            return user_balance
        elif bet_string in ['a', 'all', 'allin']:
            return user_balance
        
        # Handle percentage of balance
        if bet_string.endswith('%'):
            try:
                percentage = float(bet_string[:-1])
                if 0 <= percentage <= 100:
                    return int(user_balance * percentage / 100)
            except ValueError:
                pass
        
        # Handle numeric suffixes (k, m, b)
        multipliers = {
            'k': 1_000,
            'm': 1_000_000,
            'b': 1_000_000_000
        }
        
        for suffix, multiplier in multipliers.items():
            if bet_string.endswith(suffix):
                try:
                    base_amount = float(bet_string[:-1])
                    return int(base_amount * multiplier)
                except ValueError:
                    continue
        
        # Handle regular numbers (including decimals)
        try:
            return int(float(bet_string))
        except ValueError:
            pass
        
        # Handle comma-separated numbers
        if ',' in bet_string:
            try:
                # Remove commas and parse
                clean_string = bet_string.replace(',', '')
                return int(float(clean_string))
            except ValueError:
                pass
        
        return 0
        
    except Exception as e:
        logger.error(f"Bet parsing error: {e}")
        return 0

def validate_username(username: str) -> bool:
    """
    Validate username format
    
    Args:
        username: Username to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic username validation
        if not username or len(username) < 2 or len(username) > 32:
            return False
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Username validation error: {e}")
        return False

def sanitize_input(input_string: str, max_length: int = 100) -> str:
    """
    Sanitize user input string
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    try:
        if not input_string:
            return ""
        
        # Truncate to max length
        sanitized = input_string[:max_length]
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Input sanitization error: {e}")
        return ""

def validate_color_prediction(prediction: str) -> bool:
    """
    Validate color prediction for games like roulette
    
    Args:
        prediction: Color prediction string
    
    Returns:
        True if valid, False otherwise
    """
    valid_colors = ['red', 'black', 'green', 'r', 'b', 'g']
    return prediction.lower().strip() in valid_colors

def validate_number_range(number: Union[int, str], min_val: int, max_val: int) -> bool:
    """
    Validate if a number is within a specified range
    
    Args:
        number: Number to validate (can be string)
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        True if valid, False otherwise
    """
    try:
        num = int(number)
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False

def format_coins(amount: int) -> str:
    """
    Format coin amount for display
    
    Args:
        amount: Coin amount
    
    Returns:
        Formatted string
    """
    try:
        if amount >= 1_000_000_000:
            return f"{amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"{amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount / 1_000:.1f}K"
        else:
            return f"{amount:,}"
    except Exception as e:
        logger.error(f"Coin formatting error: {e}")
        return str(amount)

def validate_prediction_format(prediction: str, game_type: str) -> bool:
    """
    Validate prediction format for specific games
    
    Args:
        prediction: Prediction string
        game_type: Type of game (coinflip, roulette, etc.)
    
    Returns:
        True if valid format, False otherwise
    """
    try:
        prediction = prediction.lower().strip()
        
        if game_type == "coinflip":
            return prediction in ['heads', 'tails', 'h', 't']
        
        elif game_type == "roulette":
            # Basic roulette validation (more specific validation in game logic)
            if prediction in ['red', 'black', 'green', 'even', 'odd']:
                return True
            if prediction in ['0', '00'] or (prediction.isdigit() and 1 <= int(prediction) <= 36):
                return True
            return bool(re.match(r'^[\d,\-\s]+$', prediction))
        
        elif game_type == "dice":
            return prediction.isdigit() and 1 <= int(prediction) <= 20
        
        return True
        
    except Exception as e:
        logger.error(f"Prediction validation error: {e}")
        return False

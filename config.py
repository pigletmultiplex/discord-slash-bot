"""
Configuration settings for the Discord Gambling Bot
"""
import os
from server.db import *
from dotenv import load_dotenv
load_dotenv()

# Bot Configuration
BOT_PREFIX = "!, /"
BOT_DESCRIPTION = "A Discord gambling bot with various casino games"

# Game Settings
DEFAULT_STARTING_BALANCE = 1000
DAILY_BONUS_AMOUNT = 500

# Cooldown Settings (in seconds)
GAME_COOLDOWNS = {
    'blackjack': 30,
    'coinflip': 15,
    'slots': 20,
    'roulette': 25,
    'crash': 35,
    'poker': 45,
    'race': 30,
    'roll': 10,
    'sevens': 20,
    'rockpaperscissors': 15,
    'findthelady': 25,
    'daily': 86400
}

# Betting Limits
MIN_BET = 1

# XP Settings
XP_PER_WIN = 100
XP_PER_GAME = 25

# Game Specific Settings
BLACKJACK_SETTINGS = {
    'num_decks': 6,
    'blackjack_payout': 1.5,
    'easy_mode_odds': 1.5,
    'hard_mode_odds': 2.0,
    'dealer_hits_soft_17': True
}

COINFLIP_SETTINGS = {
    'payout': 1.0,
    'outcomes': ['heads', 'tails']
}

ROULETTE_SETTINGS = {
    'wheel_type': 'american',
    'max_numbers_bet': 18,
}

SLOTS_SETTINGS = {
    'reels': 5,
    'symbols': {
        '💎': {'weight': 1, 'name': 'Diamond'},
        '🔔': {'weight': 3, 'name': 'Bell'},
        '🍇': {'weight': 8, 'name': 'Grapes'},
        '🍊': {'weight': 12, 'name': 'Orange'},
        '🍋': {'weight': 18, 'name': 'Lemon'},
        '🍒': {'weight': 25, 'name': 'Cherry'},
        '🔴': {'weight': 15, 'name': 'Red'},
        '🟡': {'weight': 18, 'name': 'Yellow'}
    }
}

# Database Settings
DATA_DIRECTORY = "data"
USERS_DATA_FILE = os.path.join(DATA_DIRECTORY, "users.json")

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Discord Settings
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')

# Security Settings
MAX_MESSAGE_LENGTH = 2000
RATE_LIMIT_PER_USER = 10

# Economy Settings
MAX_BALANCE = 999_999_999_999

# Embed Colors
COLORS = {
    'success': 0x00ff00,
    'error': 0xff0000,
    'warning': 0xffff00,
    'info': 0x0099ff,
    'gambling': 0xffd700,
    'neutral': 0x808080
}

# Game Emojis
EMOJIS = {
    'coin_heads': '🟡',
    'coin_tails': '⚫',
    'dice': '🎲',
    'cards': '🃏',
    'slots': '🎰',
    'roulette': '🎡',
    'money': '💰',
    'win': '🎉',
    'lose': '💥',
    'push': '🤝'
}

# Feature Flags
FEATURES = {
    'daily_bonus': True,
    'leaderboards': True,
    'user_stats': True
}

# Maintenance Mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "🔧 The bot is currently under maintenance. Please try again later."

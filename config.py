"""
Configuration settings for the Discord Gambling Bot
"""
import os
from os import getenv
from dotenv import load_dotenv
load_dotenv()

# Bot Configuration
BOT_PREFIX = "$, !, ., /, ?, >, <, @, #, %, ^, &, *, (, ), _, +, =, -, [, ], {, }, |, \, :, ;, ',"
BOT_DESCRIPTION = "A Discord gambling bot with various casino games"

# Game Settings
DEFAULT_STARTING_BALANCE = 1000
DAILY_BONUS_AMOUNT = 500
DAILY_BONUS_COOLDOWN = 86400  # 24 hours in seconds

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
    'daily': 86400  # 24 hours
}

# Betting Limits
MIN_BET = 1
MAX_BET_MULTIPLIER = 1.0  # Fraction of user's balance they can bet at once

# XP Settings
XP_PER_WIN = 100
XP_PER_GAME = 25

# Game Specific Settings
BLACKJACK_SETTINGS = {
    'num_decks': 6,
    'blackjack_payout': 1.5,  # 3:2 payout
    'easy_mode_odds': 1.5,    # 3:2
    'hard_mode_odds': 2.0,    # 2:1
    'dealer_hits_soft_17': True
}

COINFLIP_SETTINGS = {
    'payout': 1.0,  # 1:1 payout
    'outcomes': ['heads', 'tails']
}

ROULETTE_SETTINGS = {
    'wheel_type': 'american',  # american (0, 00) or european (0 only)
    'max_numbers_bet': 18,     # Maximum numbers that can be bet on at once
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
BACKUP_INTERVAL = 3600  # Backup every hour

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Discord Settings
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
COMMAND_SYNC_GUILDS = []  # Leave empty to sync globally

# Security Settings
MAX_MESSAGE_LENGTH = 2000
RATE_LIMIT_PER_USER = 10  # Commands per minute
ADMIN_USER_IDS = []  # List of admin user IDs

# Economy Settings
INFLATION_PROTECTION = True
MAX_BALANCE = 999_999_999_999  # Maximum balance a user can have

# Embed Colors (Discord color codes)
COLORS = {
    'success': 0x00ff00,    # Green
    'error': 0xff0000,      # Red
    'warning': 0xffff00,    # Yellow
    'info': 0x0099ff,       # Blue
    'gambling': 0xffd700,   # Gold
    'neutral': 0x808080     # Gray
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
    'user_stats': True,
    'game_history': False,
    'achievements': False,
    'referral_system': False
}

# API Settings (for future expansion)
API_SETTINGS = {
    'rate_limit': 100,  # Requests per hour
    'timeout': 30,      # Request timeout in seconds
}

# Maintenance Mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "🔧 The bot is currently under maintenance. Please try again later."

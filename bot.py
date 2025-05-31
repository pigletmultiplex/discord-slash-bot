"""
Main Discord bot class with slash commands
"""
import discord
from discord.ext import commands
import logging
import json
import os
from datetime import datetime, timedelta

from economy import EconomyManager
from games.blackjack import BlackjackGame
from games.coinflip import CoinflipGame
from games.slots import SlotsGame
from games.roulette import RouletteGame
from games.poker import PokerGame
from utils.cooldowns import CooldownManager
from utils.validators import validate_bet, parse_bet_amount
from utils.achievements import AchievementManager
from utils.imagegenerator import ProfileBadgeGenerator
from utils.admin import AdminManager
from config import *

logger = logging.getLogger(__name__)

class GamblingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="A Discord gambling bot with various casino games"
        )
        
        # Initialize managers
        self.economy = EconomyManager()
        self.cooldowns = CooldownManager()
        self.achievements = AchievementManager()
        self.badge_generator = ProfileBadgeGenerator()
        self.admin = AdminManager(self.economy, self.achievements)
        
        # Initialize games
        self.blackjack = BlackjackGame()
        self.coinflip = CoinflipGame()
        self.slots = SlotsGame()
        self.roulette = RouletteGame()
        self.poker = PokerGame()

    async def setup_hook(self):
        """Called when the bot is starting up"""
        try:
            # Set up default admin (you can change this in config)
            # Replace with actual admin user IDs
            default_admin_ids = ["123456789012345678"]  # Add your Discord user ID here
            for admin_id in default_admin_ids:
                self.admin.add_admin(admin_id)
            
            # Register slash commands first
            await setup_commands(self)
            # Sync slash commands
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="🎰 Casino Games | Use /help")
        )

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing required argument. Check command usage.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("❌ An error occurred while processing your command.")

# Slash command implementations
@discord.app_commands.describe(
    bet="The amount to bet. Use 'm' for max balance",
    mode="Toggle hard mode (default: Easy Mode)"
)
async def blackjack_command(interaction: discord.Interaction, bet: str, mode: str = "easy"):
    """Play a game of Blackjack (aka 21)"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check cooldown
        if bot.cooldowns.is_on_cooldown(user_id, 'blackjack'):
            remaining = bot.cooldowns.get_remaining_cooldown(user_id, 'blackjack')
            await interaction.response.send_message(
                f"⏰ Blackjack is on cooldown. Try again in {remaining:.1f}s",
                ephemeral=True
            )
            return
        
        # Validate and parse bet
        user_balance = bot.economy.get_balance(user_id)
        bet_amount = parse_bet_amount(bet, user_balance)
        
        if not validate_bet(bet_amount, user_balance):
            await interaction.response.send_message(
                f"❌ Invalid bet. Your balance: {user_balance:,} coins",
                ephemeral=True
            )
            return
        
        # Start blackjack game
        hard_mode = mode.lower() in ['hard', 'h']
        game_result = await bot.blackjack.play_game(interaction, bet_amount, hard_mode)
        
        # Process result
        if game_result['won']:
            winnings = game_result['winnings']
            bot.economy.add_balance(user_id, winnings)
            bot.economy.add_xp(user_id, 100)
        else:
            bot.economy.subtract_balance(user_id, bet_amount)
        
        # Set cooldown
        bot.cooldowns.set_cooldown(user_id, 'blackjack', GAME_COOLDOWNS['blackjack'])
        
    except Exception as e:
        logger.error(f"Blackjack command error: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    prediction="Choose heads or tails",
    bet="The amount to bet. Use 'm' for max balance"
)
async def coinflip_command(interaction: discord.Interaction, prediction: str, bet: str):
    """Flip a coin and bet on the outcome!"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check cooldown
        if bot.cooldowns.is_on_cooldown(user_id, 'coinflip'):
            remaining = bot.cooldowns.get_remaining_cooldown(user_id, 'coinflip')
            await interaction.response.send_message(
                f"⏰ Coinflip is on cooldown. Try again in {remaining:.1f}s",
                ephemeral=True
            )
            return
        
        # Validate prediction
        if prediction.lower() not in ['heads', 'tails', 'h', 't']:
            await interaction.response.send_message(
                "❌ Invalid prediction. Use 'heads', 'tails', 'h', or 't'",
                ephemeral=True
            )
            return
        
        # Validate and parse bet
        user_balance = bot.economy.get_balance(user_id)
        bet_amount = parse_bet_amount(bet, user_balance)
        
        if not validate_bet(bet_amount, user_balance):
            await interaction.response.send_message(
                f"❌ Invalid bet. Your balance: {user_balance:,} coins",
                ephemeral=True
            )
            return
        
        # Play coinflip
        result = await bot.coinflip.play_game(interaction, prediction, bet_amount)
        
        # Process result
        if result['won']:
            winnings = result['winnings']
            bot.economy.add_balance(user_id, winnings)
            bot.economy.add_xp(user_id, 100)
        else:
            bot.economy.subtract_balance(user_id, bet_amount)
        
        # Set cooldown
        bot.cooldowns.set_cooldown(user_id, 'coinflip', GAME_COOLDOWNS['coinflip'])
        
    except Exception as e:
        logger.error(f"Coinflip command error: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    bet="The amount to bet. Use 'm' for max balance"
)
async def slots_command(interaction: discord.Interaction, bet: str):
    """Try your luck in the slots!"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check cooldown
        if bot.cooldowns.is_on_cooldown(user_id, 'slots'):
            remaining = bot.cooldowns.get_remaining_cooldown(user_id, 'slots')
            await interaction.response.send_message(
                f"⏰ Slots is on cooldown. Try again in {remaining:.1f}s",
                ephemeral=True
            )
            return
        
        # Validate and parse bet
        user_balance = bot.economy.get_balance(user_id)
        bet_amount = parse_bet_amount(bet, user_balance)
        
        if not validate_bet(bet_amount, user_balance):
            await interaction.response.send_message(
                f"❌ Invalid bet. Your balance: {user_balance:,} coins",
                ephemeral=True
            )
            return
        
        # Play slots
        result = await bot.slots.play_game(interaction, bet_amount)
        
        # Process result
        if result['won']:
            winnings = result['winnings']
            bot.economy.add_balance(user_id, winnings)
            bot.economy.add_xp(user_id, 50)
        else:
            bot.economy.subtract_balance(user_id, bet_amount)
        
        # Set cooldown
        bot.cooldowns.set_cooldown(user_id, 'slots', GAME_COOLDOWNS['slots'])
        
    except Exception as e:
        logger.error(f"Slots command error: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    prediction="What to bet on (red, black, numbers, etc.)",
    bet="The amount to bet. Use 'm' for max balance"
)
async def roulette_command(interaction: discord.Interaction, prediction: str, bet: str):
    """Play a game of roulette!"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check cooldown
        if bot.cooldowns.is_on_cooldown(user_id, 'roulette'):
            remaining = bot.cooldowns.get_remaining_cooldown(user_id, 'roulette')
            await interaction.response.send_message(
                f"⏰ Roulette is on cooldown. Try again in {remaining:.1f}s",
                ephemeral=True
            )
            return
        
        # Validate and parse bet
        user_balance = bot.economy.get_balance(user_id)
        bet_amount = parse_bet_amount(bet, user_balance)
        
        if not validate_bet(bet_amount, user_balance):
            await interaction.response.send_message(
                f"❌ Invalid bet. Your balance: {user_balance:,} coins",
                ephemeral=True
            )
            return
        
        # Play roulette
        result = await bot.roulette.play_game(interaction, prediction, bet_amount)
        
        # Process result
        if result['won']:
            winnings = result['winnings']
            bot.economy.add_balance(user_id, winnings)
            bot.economy.add_xp(user_id, 75)
        else:
            bot.economy.subtract_balance(user_id, bet_amount)
        
        # Set cooldown
        bot.cooldowns.set_cooldown(user_id, 'roulette', GAME_COOLDOWNS['roulette'])
        
    except Exception as e:
        logger.error(f"Roulette command error: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    ante="The ante bet amount. Use 'm' for max balance",
    bonus="Optional bonus bet amount",
    all_in="Play all-in mode for 2x payout (skips betting rounds)"
)
async def poker_command(interaction: discord.Interaction, ante: str, bonus: str = "0", all_in: bool = False):
    """Play Texas Hold'em Bonus Poker against the dealer"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check cooldown
        if bot.cooldowns.is_on_cooldown(user_id, 'poker'):
            remaining = bot.cooldowns.get_remaining_cooldown(user_id, 'poker')
            await interaction.response.send_message(
                f"⏰ Poker is on cooldown. Try again in {remaining:.1f}s",
                ephemeral=True
            )
            return
        
        # Validate and parse bets
        user_balance = bot.economy.get_balance(user_id)
        ante_amount = parse_bet_amount(ante, user_balance)
        bonus_amount = parse_bet_amount(bonus, user_balance) if bonus != "0" else 0
        
        total_bet = ante_amount + bonus_amount
        if not validate_bet(ante_amount, user_balance) or total_bet > user_balance:
            await interaction.response.send_message(
                f"❌ Invalid bet. Your balance: {user_balance:,} coins",
                ephemeral=True
            )
            return
        
        # Deduct bets from balance
        bot.economy.subtract_balance(user_id, total_bet)
        
        # Play poker
        result = await bot.poker.play_game(interaction, ante_amount, bonus_amount, all_in)
        
        # Process result
        if result['won']:
            winnings = result['winnings']
            bot.economy.add_balance(user_id, winnings)
            bot.economy.add_xp(user_id, 150)  # Higher XP for poker
            bot.economy.record_game(user_id, True, winnings)
        else:
            bot.economy.record_game(user_id, False)
        
        # Set cooldown
        bot.cooldowns.set_cooldown(user_id, 'poker', GAME_COOLDOWNS['poker'])
        
    except Exception as e:
        logger.error(f"Poker command error: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe()
async def balance_command(interaction: discord.Interaction):
    """Check your current balance and statistics"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Get user data and stats
        user_data = bot.economy.get_user_data(user_id)
        stats = bot.economy.get_user_stats(user_id)
        
        # Get achievements
        user_achievements = bot.achievements.get_user_achievements(user_data)
        progress = bot.achievements.get_achievement_progress(user_data)
        
        embed = discord.Embed(
            title=f"🏆 {interaction.user.display_name}'s Profile",
            color=discord.Color.gold()
        )
        
        # Basic stats
        embed.add_field(name="Balance", value=f"{user_data['balance']:,} coins", inline=True)
        embed.add_field(name="XP", value=f"{user_data['xp']:,}", inline=True)
        embed.add_field(name="Achievements", value=f"{len(user_achievements)} unlocked", inline=True)
        
        # Game stats
        embed.add_field(name="Games Played", value=f"{stats['games_played']:,}", inline=True)
        embed.add_field(name="Win Rate", value=f"{stats['win_rate']:.1f}%", inline=True)
        embed.add_field(name="Win Streak", value=f"{user_data.get('current_win_streak', 0)}", inline=True)
        
        # Financial stats
        embed.add_field(name="Total Winnings", value=f"{stats['total_winnings']:,} coins", inline=True)
        embed.add_field(name="Biggest Win", value=f"{user_data.get('biggest_win', 0):,} coins", inline=True)
        embed.add_field(name="Total Losses", value=f"{stats['total_losses']:,} coins", inline=True)
        
        # Show recent achievements
        if user_achievements:
            recent_achievements = user_achievements[-3:]  # Last 3 earned
            achievement_text = " | ".join([f"{ach.icon} {ach.name}" for ach in recent_achievements])
            embed.add_field(name="Recent Achievements", value=achievement_text, inline=False)
        
        embed.set_footer(text=f"Member since: {user_data['created_at'][:10]} | Use /profile for detailed view")
        
        # Generate profile badge image
        try:
            badge_image = bot.badge_generator.create_profile_badge(user_data, user_achievements, progress)
            file = discord.File(badge_image, filename="profile_badges.png")
            embed.set_image(url="attachment://profile_badges.png")
            
            await interaction.response.send_message(embed=embed, file=file)
        except Exception as img_error:
            logger.error(f"Failed to generate profile badge: {img_error}")
            # Fallback to text-only
            await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Balance command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe()
async def profile_command(interaction: discord.Interaction):
    """View your detailed achievement profile with badges"""
    try:
        user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Get user data and achievements
        user_data = bot.economy.get_user_data(user_id)
        user_achievements = bot.achievements.get_user_achievements(user_data)
        progress = bot.achievements.get_achievement_progress(user_data)
        
        # Create detailed profile embed
        embed = discord.Embed(
            title=f"🏆 {interaction.user.display_name}'s Achievement Profile",
            description=f"**{len(user_achievements)}** achievements unlocked out of **{len(bot.achievements.achievements)}** total",
            color=discord.Color.gold()
        )
        
        # Show achievement breakdown by category
        balance_achievements = [a for a in user_achievements if 'rich' in a.id]
        game_achievements = [a for a in user_achievements if 'gamer' in a.id]
        win_achievements = [a for a in user_achievements if 'winner' in a.id or 'bigwin' in a.id]
        
        embed.add_field(
            name="💰 Wealth Achievements", 
            value=f"{len(balance_achievements)} unlocked", 
            inline=True
        )
        embed.add_field(
            name="🎮 Gaming Achievements", 
            value=f"{len(game_achievements)} unlocked", 
            inline=True
        )
        embed.add_field(
            name="🏆 Victory Achievements", 
            value=f"{len(win_achievements)} unlocked", 
            inline=True
        )
        
        # Show progress towards next achievements
        closest_achievements = [(aid, prog) for aid, prog in progress.items() 
                              if not prog['completed'] and prog['percentage'] > 0]
        closest_achievements.sort(key=lambda x: x[1]['percentage'], reverse=True)
        
        if closest_achievements:
            next_achievements = closest_achievements[:3]
            progress_text = "\n".join([
                f"{bot.achievements.achievements[aid].icon} **{bot.achievements.achievements[aid].name}**: {prog['current']}/{prog['target']} ({prog['percentage']:.0f}%)"
                for aid, prog in next_achievements
            ])
            embed.add_field(name="🎯 Closest to Unlock", value=progress_text, inline=False)
        
        # Generate and attach profile badge image
        try:
            badge_image = bot.badge_generator.create_profile_badge(user_data, user_achievements, progress)
            file = discord.File(badge_image, filename="achievement_profile.png")
            embed.set_image(url="attachment://achievement_profile.png")
            
            await interaction.response.send_message(embed=embed, file=file)
        except Exception as img_error:
            logger.error(f"Failed to generate achievement profile: {img_error}")
            # Fallback to text-only display
            await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Profile command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

# Admin Commands
@discord.app_commands.describe(
    user_id="Discord user ID to check",
)
async def admin_user_command(interaction: discord.Interaction, user_id: str):
    """View detailed information about a specific user (Admin only)"""
    try:
        admin_user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check admin permissions
        if not bot.admin.is_admin(admin_user_id):
            await interaction.response.send_message("❌ You don't have permission to use admin commands", ephemeral=True)
            return
        
        # Get user details
        user_details = bot.admin.get_user_details(user_id)
        user_data = user_details["user_data"]
        
        embed = discord.Embed(
            title=f"👤 User Details - {user_id}",
            color=discord.Color.red()
        )
        
        # Basic info
        embed.add_field(name="Balance", value=f"{user_data['balance']:,} coins", inline=True)
        embed.add_field(name="XP", value=f"{user_data['xp']:,}", inline=True)
        embed.add_field(name="Games Played", value=f"{user_data['games_played']:,}", inline=True)
        
        # Status info
        banned_status = "🚫 Banned" if user_data.get("banned", False) else "✅ Active"
        embed.add_field(name="Status", value=banned_status, inline=True)
        
        if user_data.get("banned", False):
            embed.add_field(name="Ban Reason", value=user_data.get("ban_reason", "No reason"), inline=True)
        
        # Achievement info
        embed.add_field(
            name="Achievements", 
            value=f"{user_details['achievement_count']}/{user_details['total_achievements']}", 
            inline=True
        )
        
        # Statistics
        win_rate = (user_data.get('games_won', 0) / user_data['games_played'] * 100) if user_data['games_played'] > 0 else 0
        embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
        embed.add_field(name="Total Winnings", value=f"{user_data.get('total_winnings', 0):,} coins", inline=True)
        embed.add_field(name="Total Losses", value=f"{user_data.get('total_losses', 0):,} coins", inline=True)
        
        embed.add_field(name="Created", value=user_data.get('created_at', 'Unknown')[:10], inline=True)
        embed.add_field(name="Last Active", value=user_data.get('last_active', 'Unknown')[:10], inline=True)
        
        embed.set_footer(text="Admin Panel | User Details")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Admin user command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe()
async def admin_stats_command(interaction: discord.Interaction):
    """View bot statistics and health (Admin only)"""
    try:
        admin_user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check admin permissions
        if not bot.admin.is_admin(admin_user_id):
            await interaction.response.send_message("❌ You don't have permission to use admin commands", ephemeral=True)
            return
        
        # Get bot statistics
        stats = bot.admin.get_bot_statistics()
        health = bot.admin.get_system_health()
        
        embed = discord.Embed(
            title="📊 Bot Statistics Dashboard",
            color=discord.Color.red()
        )
        
        # Basic stats
        embed.add_field(name="Uptime", value=stats["uptime"], inline=True)
        embed.add_field(name="Total Users", value=f"{stats['total_users']:,}", inline=True)
        embed.add_field(name="Active Users", value=f"{stats['active_users']:,}", inline=True)
        
        # Economy stats
        embed.add_field(name="Total Balance", value=f"{stats['total_balance']:,} coins", inline=True)
        embed.add_field(name="Total Games", value=f"{stats['total_games']:,}", inline=True)
        embed.add_field(name="Commands Executed", value=f"{stats['commands_executed']:,}", inline=True)
        
        # Financial flow
        embed.add_field(name="Total Winnings", value=f"{stats['total_winnings']:,} coins", inline=True)
        embed.add_field(name="Total Losses", value=f"{stats['total_losses']:,} coins", inline=True)
        embed.add_field(name="Net Flow", value=f"{stats['net_flow']:,} coins", inline=True)
        
        # Top players
        if stats["top_balance"]:
            top_balance_text = "\n".join([
                f"<@{uid}>: {udata.get('balance', 0):,} coins"
                for uid, udata in stats["top_balance"][:3]
            ])
            embed.add_field(name="Top Balance", value=top_balance_text, inline=False)
        
        # System health
        health_status = "🟢 Healthy" if health["status"] == "healthy" else "🔴 Unhealthy"
        embed.add_field(name="System Health", value=health_status, inline=True)
        
        embed.set_footer(text="Admin Panel | Bot Statistics")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Admin stats command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    user_id="Discord user ID to modify",
    amount="Amount to add/subtract (use negative for subtraction)",
    reason="Reason for the balance change"
)
async def admin_balance_command(interaction: discord.Interaction, user_id: str, amount: int, reason: str = "Admin adjustment"):
    """Modify a user's balance (Admin only)"""
    try:
        admin_user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check admin permissions
        if not bot.admin.is_admin(admin_user_id):
            await interaction.response.send_message("❌ You don't have permission to use admin commands", ephemeral=True)
            return
        
        # Modify balance
        change_log = bot.admin.modify_user_balance(user_id, amount, reason)
        
        embed = discord.Embed(
            title="💰 Balance Modified",
            color=discord.Color.green() if amount > 0 else discord.Color.red()
        )
        
        embed.add_field(name="User", value=f"<@{user_id}>", inline=True)
        embed.add_field(name="Old Balance", value=f"{change_log['old_balance']:,} coins", inline=True)
        embed.add_field(name="New Balance", value=f"{change_log['new_balance']:,} coins", inline=True)
        embed.add_field(name="Change", value=f"{change_log['change']:+,} coins", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        embed.set_footer(text=f"Modified by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Admin balance command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    user_id="Discord user ID to ban",
    reason="Reason for the ban"
)
async def admin_ban_command(interaction: discord.Interaction, user_id: str, reason: str = "Banned by admin"):
    """Ban a user from using the bot (Admin only)"""
    try:
        admin_user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check admin permissions
        if not bot.admin.is_admin(admin_user_id):
            await interaction.response.send_message("❌ You don't have permission to use admin commands", ephemeral=True)
            return
        
        # Ban user
        success = bot.admin.ban_user(user_id, reason)
        
        if success:
            embed = discord.Embed(
                title="🚫 User Banned",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Banned by {interaction.user.display_name}")
        else:
            embed = discord.Embed(
                title="❌ Ban Failed",
                description="Could not ban the user",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Admin ban command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe(
    user_id="Discord user ID to unban"
)
async def admin_unban_command(interaction: discord.Interaction, user_id: str):
    """Unban a user (Admin only)"""
    try:
        admin_user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check admin permissions
        if not bot.admin.is_admin(admin_user_id):
            await interaction.response.send_message("❌ You don't have permission to use admin commands", ephemeral=True)
            return
        
        # Unban user
        success = bot.admin.unban_user(user_id)
        
        if success:
            embed = discord.Embed(
                title="✅ User Unbanned",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=f"<@{user_id}>", inline=True)
            embed.set_footer(text=f"Unbanned by {interaction.user.display_name}")
        else:
            embed = discord.Embed(
                title="❌ Unban Failed",
                description="Could not unban the user",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Admin unban command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

@discord.app_commands.describe()
async def admin_backup_command(interaction: discord.Interaction):
    """Create a backup of bot data (Admin only)"""
    try:
        admin_user_id = str(interaction.user.id)
        bot = interaction.client
        
        # Check admin permissions
        if not bot.admin.is_admin(admin_user_id):
            await interaction.response.send_message("❌ You don't have permission to use admin commands", ephemeral=True)
            return
        
        # Create backup
        backup_result = bot.admin.backup_data()
        
        if backup_result["success"]:
            embed = discord.Embed(
                title="💾 Backup Created",
                color=discord.Color.green()
            )
            embed.add_field(name="Filename", value=backup_result["filename"], inline=True)
            embed.add_field(name="Users Backed Up", value=f"{backup_result['users_backed_up']:,}", inline=True)
            embed.add_field(name="Timestamp", value=backup_result["timestamp"][:19], inline=True)
        else:
            embed = discord.Embed(
                title="❌ Backup Failed",
                description=f"Error: {backup_result['error']}",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Admin backup command error: {e}")
        await interaction.response.send_message("❌ An error occurred", ephemeral=True)

# Register slash commands
async def setup_commands(bot: GamblingBot):
    """Setup all slash commands"""
    bot.tree.add_command(discord.app_commands.Command(
        name="blackjack",
        description="Play a game of Blackjack (aka 21)",
        callback=blackjack_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="coinflip",
        description="Flip a coin and bet on the outcome!",
        callback=coinflip_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="slots",
        description="Try your luck in the slots!",
        callback=slots_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="roulette",
        description="Play a game of roulette!",
        callback=roulette_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="poker",
        description="Play Texas Hold'em Bonus Poker against the dealer",
        callback=poker_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="balance",
        description="Check your current balance and statistics",
        callback=balance_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="profile",
        description="View your detailed achievement profile with badges",
        callback=profile_command
    ))
    
    # Admin commands
    bot.tree.add_command(discord.app_commands.Command(
        name="admin-user",
        description="View detailed information about a specific user (Admin only)",
        callback=admin_user_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="admin-stats",
        description="View bot statistics and health (Admin only)",
        callback=admin_stats_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="admin-balance",
        description="Modify a user's balance (Admin only)",
        callback=admin_balance_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="admin-ban",
        description="Ban a user from using the bot (Admin only)",
        callback=admin_ban_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="admin-unban",
        description="Unban a user (Admin only)",
        callback=admin_unban_command
    ))
    
    bot.tree.add_command(discord.app_commands.Command(
        name="admin-backup",
        description="Create a backup of bot data (Admin only)",
        callback=admin_backup_command
    ))

# Initialize commands when bot starts
async def main():
    bot = GamblingBot()
    await setup_commands(bot)
    return bot

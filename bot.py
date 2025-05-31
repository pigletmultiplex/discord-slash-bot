"""
Main Discord bot class with slash commands
"""
from sys import prefix
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

class Handlers(commands.Cog, name='handlers'):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(self.client.user.name + " is ready")
        try:
            await self.client.change_presence(
                activity=discord.Game(f"blackjack | {prefix}help")
            )
        except:
            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if hasattr(ctx.command, 'on_error'):
            return

        from discord.ext.commands.errors import (
            CommandInvokeError, CommandNotFound, MissingRequiredArgument,
            TooManyArguments, BadArgument, UserNotFound, MemberNotFound,
            MissingPermissions, BotMissingPermissions, CommandOnCooldown
        )

        # Custom exception for insufficient funds
        class InsufficientFundsException(Exception):
            pass

        if isinstance(error, CommandInvokeError):
            await self.on_command_error(ctx, error.original)
        
        elif isinstance(error, CommandNotFound):
            await ctx.invoke(self.client.get_command('help'))

        elif isinstance(error, (MissingRequiredArgument,
                                TooManyArguments, BadArgument)):
            await ctx.invoke(self.client.get_command('help'), ctx.command.name)

        elif isinstance(error, (UserNotFound, MemberNotFound)):
            await ctx.send(f"Member, `{error.argument}`, was not found.")

        elif isinstance(error, MissingPermissions):
            await ctx.send("Must have following permission(s): " + 
            ", ".join([f'`{perm}`' for perm in error.missing_perms]))

        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I must have following permission(s): " +
            ", ".join([f'`{perm}`' for perm in error.missing_perms]))

        elif isinstance(error, InsufficientFundsException):
            await ctx.invoke(self.client.get_command('money'))

        elif isinstance(error, CommandOnCooldown):
            s = int(error.retry_after)
            s = s % (24 * 3600)
            h = s // 3600
            s %= 3600
            m = s // 60
            s %= 60
            await ctx.send(f'{h}hrs {m}min {s}sec remaining.')
        
        else:
            raise error

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
            # Register Handlers cog
            await self.add_cog(Handlers(self))
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

from discord import app_commands

# -- General (GamblingHelpers) slash command implementations --

@app_commands.describe(
    user_id="User ID to set money/credits for",
    money="Amount of money to set",
    credits="Amount of credits to set"
)
async def set_command(interaction: discord.Interaction, user_id: str = None, money: int = 0, credits: int = 0):
    """[Admin/Owner] Set a user's money or credits"""
    bot = interaction.client
    admin_user_id = str(interaction.user.id)
    # Only allow owner or admin
    if not bot.admin.is_admin(admin_user_id):
        await interaction.response.send_message("❌ You don't have permission to use this command", ephemeral=True)
        return
    if not user_id:
        await interaction.response.send_message("❌ You must specify a user_id", ephemeral=True)
        return
    if money:
        bot.economy.set_balance(str(user_id), money)
    # If credits tracking is implemented, add it here
    await interaction.response.send_message(f"✅ Updated user {user_id}'s balance.", ephemeral=True)

@app_commands.describe()
async def add_command(interaction: discord.Interaction):
    """Get free money once every cooldown period"""
    bot = interaction.client
    user_id = str(interaction.user.id)
    # You may define these constants elsewhere or set as fixed values here
    amount = 1000  # DEFAULT_BET * B_MULT
    cooldown_hours = 12  # B_COOLDOWN
    cooldown_seconds = cooldown_hours * 3600
    # Use CooldownManager to enforce cooldown
    if bot.cooldowns.is_on_cooldown(user_id, 'add_command'):
        remaining = bot.cooldowns.get_remaining_cooldown(user_id, 'add_command')
        await interaction.response.send_message(
            f"⏰ You can use this again in {int(remaining // 3600)}h {(int(remaining) % 3600)//60}m.",
            ephemeral=True
        )
        return
    bot.economy.add_balance(user_id, amount)
    bot.cooldowns.set_cooldown(user_id, 'add_command', cooldown_seconds)
    await interaction.response.send_message(f"Added ${amount:,}. Come back in {cooldown_hours}hrs!", ephemeral=True)

@app_commands.describe(
    user="User to check money for (leave blank for yourself)"
)
async def money_command(interaction: discord.Interaction, user: discord.Member = None):
    """How much money you or someone else has"""
    bot = interaction.client
    target = user or interaction.user
    user_data = bot.economy.get_user_data(str(target.id))
    embed = discord.Embed(
        title=target.display_name,
        description=f'**${user_data["balance"]:,}**\n**{user_data.get("credits", 0):,}** credits',
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.describe()
async def leaderboard_command(interaction: discord.Interaction):
    """Shows the users with the most money"""
    bot = interaction.client
    top = bot.economy.get_leaderboard(limit=5)
    embed = discord.Embed(title='Leaderboard:', color=discord.Color.gold())
    for i, entry in enumerate(top):
        uid = entry["user_id"]
        user = bot.get_user(int(uid)) or (await bot.fetch_user(int(uid)))
        name = user.display_name if user else f"User {uid}"
        embed.add_field(
            name=f"{i+1}. {name}",
            value=f'${entry["balance"]:,}',
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=False)

@app_commands.describe(
    command="Command to get help for (leave blank for all commands)"
)
async def help_command(interaction: discord.Interaction, command: str = None):
    """Lists commands and gives info."""
    bot = interaction.client
    embed = discord.Embed(title="Commands", color=discord.Color.blue())
    file = None

    if not command:
        # List all commands (excluding hidden/admin)
        for cmd in bot.tree.get_commands():
            if not getattr(cmd, "hidden", False) and not cmd.name.startswith("admin"):
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description or "No description.",
                    inline=False
                )
        # Optionally, add a thumbnail for fun (e.g. cards image)
        try:
            fp = os.path.join(os.path.dirname(__file__), 'modules/cards/aces.png')
            if os.path.exists(fp):
                file = discord.File(fp, filename='aces.png')
                embed.set_thumbnail(url="attachment://aces.png")
        except Exception:
            pass
    else:
        # Show help for a specific command
        cmd = bot.tree.get_command(command)
        if not cmd:
            await interaction.response.send_message("❌ Command not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"/{cmd.name}",
            description=cmd.description or "No description.",
            color=discord.Color.blue()
        )
        # Show parameters if any, and usage formatting
        params = []
        usage = f"/{cmd.name}"
        if hasattr(cmd, "parameters"):
            for p in cmd.parameters:
                params.append(f"`{p.name}`")
                # Usage string with * for optional
                if p.required:
                    usage += f" <{p.name}>"
                else:
                    usage += f" *{p.name}"
        if params:
            embed.add_field(name="Parameters", value=", ".join(params), inline=False)
        embed.add_field(name="Usage:", value=f"`{usage}`", inline=False)
    await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

@app_commands.describe()
async def kill_command(interaction: discord.Interaction):
    """[Owner] Shut down the bot."""
    bot = interaction.client
    admin_user_id = str(interaction.user.id)
    if not bot.admin.is_admin(admin_user_id):
        await interaction.response.send_message("❌ You don't have permission to use this command", ephemeral=True)
        return
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    await bot.close()

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

    # General/GamblingHelpers commands
    bot.tree.add_command(discord.app_commands.Command(
        name="set",
        description="[Admin/Owner] Set a user's money or credits",
        callback=set_command
    ))
    bot.tree.add_command(discord.app_commands.Command(
        name="add",
        description="Get free money once every cooldown period",
        callback=add_command
    ))
    bot.tree.add_command(discord.app_commands.Command(
        name="money",
        description="Check how much money you or another user has",
        callback=money_command
    ))
    bot.tree.add_command(discord.app_commands.Command(
        name="leaderboard",
        description="Shows the users with the most money",
        callback=leaderboard_command
    ))

    # Help and kill commands
    bot.tree.add_command(discord.app_commands.Command(
        name="help",
        description="Lists commands and gives info.",
        callback=help_command
    ))
    bot.tree.add_command(discord.app_commands.Command(
        name="kill",
        description="[Owner] Shut down the bot.",
        callback=kill_command
    ))

# Initialize commands when bot starts
async def main():
    bot = GamblingBot()
    await setup_commands(bot)
    return bot

class Help(commands.Cog, name='help'):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command(
        brief="Lists commands and gives info.",
        usage="help *command",
        hidden=True
    )
    async def help(self, ctx, request=None):
        if not request:
            embed = discord.Embed(title="Commands", color=discord.Color.blue())
            commands_list = [
                (
                    name, [command for command in cog.get_commands()
                        if not command.hidden]
                ) for name, cog in self.client.cogs.items()
            ]
            for name, cog_commands in commands_list:
                if len(cog_commands) != 0:
                    embed.add_field(
                        name=name,
                        value='\n'.join(
                            [f'{self.client.command_prefix}{command}'
                                for command in cog_commands]
                        ),
                        inline=False
                    )
            ABS_PATH = os.path.dirname(os.path.abspath(__file__))
            fp = os.path.join(ABS_PATH, 'modules/cards/aces.png')
            file = discord.File(fp, filename='aces.png')
            embed.set_thumbnail(url=f"attachment://aces.png")
        else:
            com = self.client.get_command(request)
            if not com:
                await ctx.invoke(self.client.get_command('help'))
                return
            embed = discord.Embed(
                title=com.name,
                description=com.brief,
                color=discord.Color.blue()
            )
            embed.set_footer(text="* optional")
            embed.add_field(
                name='Usage:',
                value='`'+self.client.command_prefix+com.usage+'`'
            )
            file = None
        await ctx.send(file=file, embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx: commands.Context):
        self.client.remove_cog('handlers')
        await self.client.logout()

class GamblingHelpers(commands.Cog, name='General'):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.economy = EconomyManager()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def set(
        self,
        ctx: commands.Context,
        user_id: int = None,
        money: int = 0,
        credits: int = 0
    ):
        if money:
            self.economy.set_balance(str(user_id), money)
        # If credits tracking is implemented, add it here

    @commands.command(
        brief="Gives you $1000 once every 12hrs",
        usage="add"
    )
    @commands.cooldown(1, 12 * 3600, type=commands.BucketType.user)
    async def add(self, ctx: commands.Context):
        amount = 1000  # DEFAULT_BET * B_MULT
        self.economy.add_balance(str(ctx.author.id), amount)
        await ctx.send(f"Added ${amount} come back in 12hrs")

    @commands.command(
        brief="How much money you or someone else has",
        usage="money *[@member]",
        aliases=['credits']
    )
    async def money(self, ctx: commands.Context, user: discord.Member = None):
        target = user or ctx.author
        user_data = self.economy.get_user_data(str(target.id))
        embed = discord.Embed(
            title=target.display_name,
            description=f'**${user_data["balance"]:,}**\n**{user_data.get("credits", 0):,}** credits',
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(
        brief="Shows the user with the most money",
        usage="leaderboard",
        aliases=["top"]
    )
    async def leaderboard(self, ctx):
        top = self.economy.get_leaderboard(limit=5)
        embed = discord.Embed(title='Leaderboard:', color=discord.Color.gold())
        for i, entry in enumerate(top):
            uid = entry["user_id"]
            user = self.client.get_user(int(uid)) or (await self.client.fetch_user(int(uid)))
            name = user.display_name if user else f"User {uid}"
            embed.add_field(
                name=f"{i+1}. {name}",
                value=f'${entry["balance"]:,}',
                inline=False
            )
        await ctx.send(embed=embed)

# ...existing code...

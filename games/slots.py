"""
Slots game implementation
"""
import discord
import random
from typing import Dict, Any, List, Tuple
import logging
from utils.imagegenerator import SlotMachineImageGenerator

logger = logging.getLogger(__name__)

class SlotsGame:
    def __init__(self):
        # Slot symbols with their weights (higher weight = more common)
        self.symbols = {
            '💎': {'weight': 1, 'name': 'Diamond'},      # Rarest
            '🔔': {'weight': 3, 'name': 'Bell'},         # Very rare  
            '🍇': {'weight': 8, 'name': 'Grapes'},       # Rare
            '🍊': {'weight': 12, 'name': 'Orange'},      # Uncommon
            '🍋': {'weight': 18, 'name': 'Lemon'},       # Common
            '🍒': {'weight': 25, 'name': 'Cherry'},      # Very common
            '🔴': {'weight': 15, 'name': 'Red'},         # Common
            '🟡': {'weight': 18, 'name': 'Yellow'}       # Common
        }
        
        # Initialize image generator
        self.image_generator = SlotMachineImageGenerator()
        
        # Payout table (multiplier of bet)
        self.payouts = {
            '💎': {'3': 500, '2': 25},   # Diamond
            '🔔': {'3': 25, '2': 10},    # Bell
            '🍇': {'3': 5, '2': 3},      # Grapes
            '🍊': {'3': 3, '2': 2},      # Orange
            '🍋': {'3': 2, '2': 1},      # Lemon
            '🍒': {'3': 1, '2': 1},      # Cherry
            '🔴': {'3': 0.75, '2': 1},   # Red
            '🟡': {'3': 0.5, '2': 0.75}, # Yellow
        }
        
        # Create weighted symbol list for random selection
        self.weighted_symbols = []
        for symbol, data in self.symbols.items():
            self.weighted_symbols.extend([symbol] * data['weight'])

    def spin_reels(self) -> List[str]:
        """Spin the slot machine reels"""
        return [random.choice(self.weighted_symbols) for _ in range(5)]

    def calculate_payout(self, reels: List[str], bet_amount: int) -> Tuple[int, str, Dict[str, int]]:
        """Calculate payout and winning details"""
        # Count each symbol
        symbol_counts = {}
        for symbol in reels:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Find best payout
        best_payout = 0
        winning_symbol = None
        winning_count = 0
        
        for symbol, count in symbol_counts.items():
            if symbol in self.payouts:
                # Check for 3+ matches
                if count >= 3 and '3' in self.payouts[symbol]:
                    payout_multiplier = self.payouts[symbol]['3']
                    potential_payout = int(bet_amount * payout_multiplier)
                    if potential_payout > best_payout:
                        best_payout = potential_payout
                        winning_symbol = symbol
                        winning_count = count
                
                # Check for 2+ matches if no 3+ match found
                elif count >= 2 and '2' in self.payouts[symbol] and best_payout == 0:
                    payout_multiplier = self.payouts[symbol]['2']
                    potential_payout = int(bet_amount * payout_multiplier)
                    if potential_payout > best_payout:
                        best_payout = potential_payout
                        winning_symbol = symbol
                        winning_count = count
        
        # Create result message
        if best_payout > 0:
            symbol_name = self.symbols[winning_symbol]['name']
            result_msg = f"{winning_count}x {winning_symbol} {symbol_name}"
        else:
            result_msg = "No match"
        
        return best_payout, result_msg, symbol_counts

    async def play_game(self, interaction: discord.Interaction, bet_amount: int) -> Dict[str, Any]:
        """Play a slots game"""
        try:
            # Create initial embed
            embed = discord.Embed(
                title="🎰 Slot Machine",
                description="Spinning the reels...",
                color=discord.Color.gold()
            )
            embed.add_field(name="Bet Amount", value=f"{bet_amount:,} coins", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Add suspense
            import asyncio
            await asyncio.sleep(2)
            
            # Spin the reels
            reels = self.spin_reels()
            payout, result_msg, symbol_counts = self.calculate_payout(reels, bet_amount)
            
            # Generate slot machine image
            try:
                slot_image = self.image_generator.create_slot_machine_image(reels, payout, bet_amount)
                file = discord.File(slot_image, filename="slot_machine.png")
                
                # Create result embed with image
                if payout > 0:
                    embed.title = "🎰 Slot Machine - WINNER!"
                    embed.color = discord.Color.green()
                    multiplier = payout / bet_amount
                    embed.description = f"**{result_msg}** - {multiplier:.2f}x multiplier!"
                else:
                    embed.title = "🎰 Slot Machine"
                    embed.color = discord.Color.red()
                    embed.description = f"**{result_msg}** - Better luck next time!"
                
                # Set the image in the embed
                embed.set_image(url="attachment://slot_machine.png")
                
                # Add symbol counts for transparency
                counts_str = " | ".join([f"{symbol}:{count}" for symbol, count in symbol_counts.items() if count > 1])
                if counts_str:
                    embed.add_field(name="Symbol Counts", value=counts_str, inline=False)
                
                await interaction.edit_original_response(embed=embed, attachments=[file])
                
            except Exception as img_error:
                logger.error(f"Failed to generate slot image: {img_error}")
                # Fallback to text-based display
                reel_display = " | ".join(reels)
                
                if payout > 0:
                    embed.title = "🎰 Slot Machine - WINNER!"
                    embed.color = discord.Color.green()
                    embed.description = f"**{reel_display}**"
                    embed.add_field(name="Result", value=result_msg, inline=False)
                    embed.add_field(name="Winnings", value=f"🎉 {payout:,} coins!", inline=True)
                    
                    multiplier = payout / bet_amount
                    embed.add_field(name="Multiplier", value=f"{multiplier:.2f}x", inline=True)
                else:
                    embed.title = "🎰 Slot Machine - No Win"
                    embed.color = discord.Color.red()
                    embed.description = f"**{reel_display}**"
                    embed.add_field(name="Result", value=result_msg, inline=False)
                    embed.add_field(name="Better Luck", value="Try again!", inline=True)
                
                # Add symbol counts for transparency
                counts_str = " | ".join([f"{symbol}:{count}" for symbol, count in symbol_counts.items() if count > 1])
                if counts_str:
                    embed.add_field(name="Symbol Counts", value=counts_str, inline=False)
                
                await interaction.edit_original_response(embed=embed)
            
            return {
                "won": payout > 0,
                "winnings": payout,
                "reels": reels,
                "result": result_msg,
                "symbol_counts": symbol_counts
            }
            
        except Exception as e:
            logger.error(f"Slots game error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred", ephemeral=True)
            return {"won": False, "winnings": 0, "error": str(e)}

    def get_payout_table(self) -> discord.Embed:
        """Get payout table as an embed"""
        embed = discord.Embed(
            title="🎰 Slots Payout Table",
            description="Payouts are multipliers of your bet amount",
            color=discord.Color.gold()
        )
        
        for symbol, data in self.symbols.items():
            symbol_name = data['name']
            payouts_text = []
            
            if symbol in self.payouts:
                if '3' in self.payouts[symbol]:
                    multiplier = self.payouts[symbol]['3']
                    payouts_text.append(f"3x = {multiplier}:1")
                if '2' in self.payouts[symbol]:
                    multiplier = self.payouts[symbol]['2']
                    payouts_text.append(f"2x = {multiplier}:1")
            
            if payouts_text:
                embed.add_field(
                    name=f"{symbol} {symbol_name}",
                    value="\n".join(payouts_text),
                    inline=True
                )
        
        embed.add_field(
            name="How to Win",
            value="Get 2 or more matching symbols for a payout!\nBest matching combination wins.",
            inline=False
        )
        
        return embed

    def get_game_stats(self) -> Dict[str, Any]:
        """Get game statistics and info"""
        return {
            "name": "Slots",
            "description": "Spin the reels and match symbols for payouts",
            "min_bet": 1,
            "max_bet": None,
            "symbols": len(self.symbols),
            "max_payout": "500:1 (3 Diamonds)"
        }

    def get_multiplier(self, reels: List[str]) -> float:
        """Return the payout multiplier for the given reels"""
        # Use the same logic as calculate_payout, but just return the multiplier
        symbol_counts = {}
        for symbol in reels:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        best_multiplier = 0.0
        for symbol, count in symbol_counts.items():
            if symbol in self.payouts:
                if count >= 3 and '3' in self.payouts[symbol]:
                    m = float(self.payouts[symbol]['3'])
                    if m > best_multiplier:
                        best_multiplier = m
                elif count >= 2 and '2' in self.payouts[symbol] and best_multiplier == 0.0:
                    m = float(self.payouts[symbol]['2'])
                    if m > best_multiplier:
                        best_multiplier = m
        return best_multiplier

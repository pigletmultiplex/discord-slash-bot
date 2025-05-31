"""
Roulette game implementation
"""
import discord
import random
import re
from typing import Dict, Any, List, Set
import logging

logger = logging.getLogger(__name__)

class RouletteGame:
    def __init__(self):
        # American roulette wheel (0, 00, 1-36)
        self.numbers = list(range(0, 37)) + [37]  # 37 represents 00
        
        # Red and black numbers (American roulette)
        self.red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.black_numbers = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        self.green_numbers = {0, 37}  # 0 and 00
        
    def spin_wheel(self) -> int:
        """Spin the roulette wheel and return result"""
        return random.choice(self.numbers)
    
    def format_number(self, number: int) -> str:
        """Format number for display"""
        if number == 37:
            return "00"
        return str(number)
    
    def get_number_color(self, number: int) -> str:
        """Get the color of a number"""
        if number in self.red_numbers:
            return "red"
        elif number in self.black_numbers:
            return "black"
        else:
            return "green"
    
    def parse_prediction(self, prediction: str) -> Dict[str, Any]:
        """Parse user prediction and return betting details"""
        prediction = prediction.lower().strip()
        
        # Single number bets
        if prediction == "0":
            return {"type": "number", "numbers": {0}, "payout": 35}
        elif prediction in ["00", "37"]:
            return {"type": "number", "numbers": {37}, "payout": 35}
        elif prediction.isdigit():
            num = int(prediction)
            if 1 <= num <= 36:
                return {"type": "number", "numbers": {num}, "payout": 35}
        
        # Color bets
        elif prediction == "red":
            return {"type": "color", "numbers": self.red_numbers, "payout": 1}
        elif prediction == "black":
            return {"type": "color", "numbers": self.black_numbers, "payout": 1}
        elif prediction == "green":
            return {"type": "color", "numbers": self.green_numbers, "payout": 17}
        
        # Half bets
        elif prediction in ["1sthalf", "1-18", "low"]:
            return {"type": "half", "numbers": set(range(1, 19)), "payout": 1}
        elif prediction in ["2ndhalf", "19-36", "high"]:
            return {"type": "half", "numbers": set(range(19, 37)), "payout": 1}
        
        # Dozen bets
        elif prediction in ["1st12", "1-12"]:
            return {"type": "dozen", "numbers": set(range(1, 13)), "payout": 2}
        elif prediction in ["2nd12", "13-24"]:
            return {"type": "dozen", "numbers": set(range(13, 25)), "payout": 2}
        elif prediction in ["3rd12", "25-36"]:
            return {"type": "dozen", "numbers": set(range(25, 37)), "payout": 2}
        
        # Column bets
        elif prediction in ["1stcol", "col1"]:
            return {"type": "column", "numbers": {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34}, "payout": 2}
        elif prediction in ["2ndcol", "col2"]:
            return {"type": "column", "numbers": {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}, "payout": 2}
        elif prediction in ["3rdcol", "col3"]:
            return {"type": "column", "numbers": {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}, "payout": 2}
        
        # Even/Odd bets
        elif prediction == "even":
            return {"type": "parity", "numbers": {n for n in range(2, 37, 2)}, "payout": 1}
        elif prediction == "odd":
            return {"type": "parity", "numbers": {n for n in range(1, 37, 2)}, "payout": 1}
        
        # Comma separated numbers
        elif "," in prediction:
            try:
                numbers = set()
                for num_str in prediction.split(","):
                    num_str = num_str.strip()
                    if num_str == "00":
                        numbers.add(37)
                    elif num_str.isdigit():
                        num = int(num_str)
                        if 0 <= num <= 36:
                            numbers.add(num)
                
                if len(numbers) > 18:  # Too many numbers, low odds
                    return {"type": "invalid", "error": "Too many numbers selected (max 18)"}
                elif len(numbers) > 0:
                    payout = max(1, 36 // len(numbers) - 1)
                    return {"type": "multiple", "numbers": numbers, "payout": payout}
            except:
                pass
        
        # Range bets (e.g., "1-10")
        elif "-" in prediction and not prediction.startswith("-"):
            try:
                parts = prediction.split("-")
                if len(parts) == 2:
                    start, end = int(parts[0]), int(parts[1])
                    if 1 <= start <= end <= 36:
                        numbers = set(range(start, end + 1))
                        if len(numbers) > 18:
                            return {"type": "invalid", "error": "Range too large (max 18 numbers)"}
                        payout = max(1, 36 // len(numbers) - 1)
                        return {"type": "range", "numbers": numbers, "payout": payout}
            except:
                pass
        
        return {"type": "invalid", "error": "Invalid prediction format"}

    async def play_game(self, interaction: discord.Interaction, prediction: str, bet_amount: int) -> Dict[str, Any]:
        """Play a roulette game"""
        try:
            # Parse the prediction
            bet_info = self.parse_prediction(prediction)
            
            if bet_info["type"] == "invalid":
                await interaction.response.send_message(
                    f"❌ {bet_info['error']}\n\nValid bets: red, black, green, 0-36, 00, ranges (1-10), lists (1,5,9), etc.",
                    ephemeral=True
                )
                return {"won": False, "winnings": 0, "error": bet_info["error"]}
            
            # Create initial embed
            embed = discord.Embed(
                title="🎡 Roulette Wheel",
                description="Spinning the wheel...",
                color=discord.Color.gold()
            )
            embed.add_field(name="Your Bet", value=prediction.title(), inline=True)
            embed.add_field(name="Bet Amount", value=f"{bet_amount:,} coins", inline=True)
            embed.add_field(name="Potential Payout", value=f"{bet_info['payout']}:1", inline=True)
            
            # Show what numbers you're betting on
            if len(bet_info["numbers"]) <= 10:
                numbers_str = ", ".join([self.format_number(n) for n in sorted(bet_info["numbers"])])
                embed.add_field(name="Numbers", value=numbers_str, inline=False)
            else:
                embed.add_field(name="Numbers", value=f"{len(bet_info['numbers'])} numbers", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            # Add suspense
            import asyncio
            await asyncio.sleep(3)
            
            # Spin the wheel
            result = self.spin_wheel()
            result_display = self.format_number(result)
            result_color = self.get_number_color(result)
            
            # Check if bet won
            won = result in bet_info["numbers"]
            winnings = bet_amount * bet_info["payout"] if won else 0
            
            # Color emojis
            color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}
            
            # Update embed with result
            if won:
                embed.title = "🎡 Roulette Wheel - WINNER!"
                embed.color = discord.Color.green()
                embed.description = f"The ball landed on **{result_display} {color_emoji[result_color]}**"
                embed.add_field(name="Result", value=f"🎉 You won {winnings:,} coins!", inline=False)
            else:
                embed.title = "🎡 Roulette Wheel - Better Luck Next Time!"
                embed.color = discord.Color.red()
                embed.description = f"The ball landed on **{result_display} {color_emoji[result_color]}**"
                embed.add_field(name="Result", value="💥 Your bet didn't win this time!", inline=False)
            
            # Add winning number details
            embed.add_field(name="Winning Number", value=f"{result_display} ({result_color.title()})", inline=True)
            
            await interaction.edit_original_response(embed=embed)
            
            return {
                "won": won,
                "winnings": winnings,
                "result": result,
                "result_display": result_display,
                "result_color": result_color,
                "prediction": prediction,
                "bet_info": bet_info
            }
            
        except Exception as e:
            logger.error(f"Roulette game error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred", ephemeral=True)
            return {"won": False, "winnings": 0, "error": str(e)}

    def get_betting_guide(self) -> discord.Embed:
        """Get betting guide as an embed"""
        embed = discord.Embed(
            title="🎡 Roulette Betting Guide",
            description="Available bet types and their payouts",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Single Numbers (35:1)",
            value="0, 1-36, 00\nExample: `15`, `0`, `00`",
            inline=False
        )
        
        embed.add_field(
            name="Colors",
            value="🔴 red (1:1)\n⚫ black (1:1)\n🟢 green (17:1)",
            inline=True
        )
        
        embed.add_field(
            name="Halves (1:1)",
            value="low/1-18 (1-18)\nhigh/19-36 (19-36)",
            inline=True
        )
        
        embed.add_field(
            name="Dozens (2:1)",
            value="1st12 (1-12)\n2nd12 (13-24)\n3rd12 (25-36)",
            inline=True
        )
        
        embed.add_field(
            name="Columns (2:1)",
            value="col1, col2, col3\n1stCol, 2ndCol, 3rdCol",
            inline=True
        )
        
        embed.add_field(
            name="Even/Odd (1:1)",
            value="even, odd",
            inline=True
        )
        
        embed.add_field(
            name="Multiple Numbers",
            value="Lists: `1,5,9,15`\nRanges: `1-10`, `20-25`",
            inline=True
        )
        
        embed.add_field(
            name="Examples",
            value="`/roulette red 100`\n`/roulette 7 500`\n`/roulette 1,3,5 200`",
            inline=False
        )
        
        return embed

    def get_game_stats(self) -> Dict[str, Any]:
        """Get game statistics and info"""
        return {
            "name": "Roulette",
            "description": "Bet on where the ball will land on the roulette wheel",
            "wheel_type": "American (0, 00, 1-36)",
            "house_edge": "5.26%",
            "min_bet": 1,
            "max_bet": None,
            "max_payout": "35:1 (Single number)"
        }

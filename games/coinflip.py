"""
Coinflip game implementation
"""
import discord
import random
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CoinflipGame:
    def __init__(self):
        self.outcomes = ['heads', 'tails']
        
    def flip_coin(self) -> str:
        """Flip a coin and return the result"""
        return random.choice(self.outcomes)
    
    def normalize_prediction(self, prediction: str) -> str:
        """Normalize user prediction"""
        prediction = prediction.lower().strip()
        
        if prediction in ['h', 'head']:
            return 'heads'
        elif prediction in ['t', 'tail']:
            return 'tails'
        elif prediction in ['heads', 'tails']:
            return prediction
        else:
            return None
    
    async def play_game(self, interaction: discord.Interaction, prediction: str, bet_amount: int) -> Dict[str, Any]:
        """Play a coinflip game"""
        try:
            # Normalize prediction
            normalized_prediction = self.normalize_prediction(prediction)
            if not normalized_prediction:
                await interaction.response.send_message(
                    "❌ Invalid prediction. Use 'heads', 'tails', 'h', or 't'",
                    ephemeral=True
                )
                return {"won": False, "winnings": 0, "error": "Invalid prediction"}
            
            # Create initial embed showing the bet
            embed = discord.Embed(
                title="🪙 Coinflip Game",
                description="Flipping the coin...",
                color=discord.Color.gold()
            )
            embed.add_field(name="Your Prediction", value=normalized_prediction.title(), inline=True)
            embed.add_field(name="Bet Amount", value=f"{bet_amount:,} coins", inline=True)
            embed.add_field(name="Potential Winnings", value=f"{bet_amount:,} coins", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Add suspense with a delay
            await asyncio.sleep(2)
            
            # Flip the coin
            result = self.flip_coin()
            won = result == normalized_prediction
            
            # Update embed with result
            if won:
                embed.title = "🪙 Coinflip Game - YOU WIN!"
                embed.color = discord.Color.green()
                embed.description = f"The coin landed on **{result.upper()}**!"
                embed.add_field(name="Result", value=f"🎉 You won {bet_amount:,} coins!", inline=False)
                winnings = bet_amount
            else:
                embed.title = "🪙 Coinflip Game - YOU LOSE!"
                embed.color = discord.Color.red()
                embed.description = f"The coin landed on **{result.upper()}**!"
                embed.add_field(name="Result", value="💥 Better luck next time!", inline=False)
                winnings = 0
            
            # Add coin emoji based on result
            coin_emoji = "🟡" if result == "heads" else "⚫"
            embed.set_thumbnail(url=None)
            embed.add_field(name="Coin", value=f"{coin_emoji} {result.title()}", inline=True)
            
            await interaction.edit_original_response(embed=embed)
            
            return {
                "won": won,
                "winnings": winnings,
                "result": result,
                "prediction": normalized_prediction
            }
            
        except Exception as e:
            logger.error(f"Coinflip game error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred", ephemeral=True)
            return {"won": False, "winnings": 0, "error": str(e)}

    def get_game_stats(self) -> Dict[str, Any]:
        """Get game statistics and info"""
        return {
            "name": "Coinflip",
            "description": "Flip a coin and bet on heads or tails",
            "odds": "1:1",
            "min_bet": 1,
            "max_bet": None,
            "house_edge": 0.0,
            "valid_predictions": ["heads", "tails", "h", "t"]
        }

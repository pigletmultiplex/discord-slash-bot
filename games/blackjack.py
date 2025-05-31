"""
Blackjack game implementation
"""
import discord
import random
import asyncio
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        
    def get_value(self) -> int:
        """Get card value for blackjack"""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Aces handled separately
        else:
            return int(self.rank)
    
    def __str__(self) -> str:
        suit_symbols = {'Hearts': '♥️', 'Diamonds': '♦️', 'Clubs': '♣️', 'Spades': '♠️'}
        return f"{self.rank}{suit_symbols[self.suit]}"

class BlackjackGame:
    def __init__(self):
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
    def create_deck(self, num_decks: int = 6) -> List[Card]:
        """Create a shuffled deck of cards"""
        deck = []
        for _ in range(num_decks):
            for suit in self.suits:
                for rank in self.ranks:
                    deck.append(Card(suit, rank))
        
        random.shuffle(deck)
        return deck
    
    def calculate_hand_value(self, hand: List[Card]) -> tuple:
        """Calculate hand value, returning (value, soft_value)"""
        value = 0
        aces = 0
        
        for card in hand:
            if card.rank == 'A':
                aces += 1
                value += 1  # Count ace as 1 initially
            else:
                value += card.get_value()
        
        # Calculate soft value (aces as 11)
        soft_value = value
        aces_as_eleven = 0
        
        # Convert aces to 11 if it doesn't bust
        while aces_as_eleven < aces and soft_value + 10 <= 21:
            soft_value += 10
            aces_as_eleven += 1
        
        return value, soft_value
    
    def format_hand(self, hand: List[Card], hard_mode: bool = False) -> str:
        """Format hand for display"""
        cards_str = " ".join(str(card) for card in hand)
        
        if hard_mode:
            return cards_str
        
        value, soft_value = self.calculate_hand_value(hand)
        
        if value == soft_value:
            return f"{cards_str} ({value})"
        else:
            return f"{cards_str} ({value}/{soft_value})"
    
    def is_blackjack(self, hand: List[Card]) -> bool:
        """Check if hand is blackjack (21 with 2 cards)"""
        if len(hand) != 2:
            return False
        
        _, soft_value = self.calculate_hand_value(hand)
        return soft_value == 21
    
    def is_bust(self, hand: List[Card]) -> bool:
        """Check if hand is bust"""
        value, _ = self.calculate_hand_value(hand)
        return value > 21
    
    def get_best_value(self, hand: List[Card]) -> int:
        """Get best possible value for hand"""
        value, soft_value = self.calculate_hand_value(hand)
        return soft_value if soft_value <= 21 else value

    async def play_game(self, interaction: discord.Interaction, bet_amount: int, hard_mode: bool = False) -> Dict[str, Any]:
        """Play a complete blackjack game"""
        try:
            deck = self.create_deck()
            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]
            
            # Check for blackjacks
            player_blackjack = self.is_blackjack(player_hand)
            dealer_blackjack = self.is_blackjack(dealer_hand)
            
            # Create initial embed
            embed = discord.Embed(
                title="🃏 Blackjack Game",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Your Hand",
                value=self.format_hand(player_hand, hard_mode),
                inline=False
            )
            embed.add_field(
                name="Dealer Hand",
                value=f"{dealer_hand[0]} ?",
                inline=False
            )
            embed.add_field(
                name="Bet",
                value=f"{bet_amount:,} coins",
                inline=True
            )
            
            # Handle blackjacks
            if player_blackjack and dealer_blackjack:
                embed.add_field(name="Result", value="🤝 Push! Both blackjack", inline=False)
                await interaction.response.send_message(embed=embed)
                return {"won": False, "winnings": 0, "push": True}
            
            if player_blackjack:
                winnings = int(bet_amount * 1.5)  # 3:2 payout for blackjack
                embed.add_field(name="Result", value=f"🎉 BLACKJACK! You win {winnings:,} coins!", inline=False)
                await interaction.response.send_message(embed=embed)
                return {"won": True, "winnings": winnings}
            
            if dealer_blackjack:
                embed.add_field(name="Dealer Hand", value=self.format_hand(dealer_hand, hard_mode), inline=False)
                embed.add_field(name="Result", value="💥 Dealer blackjack! You lose!", inline=False)
                await interaction.response.send_message(embed=embed)
                return {"won": False, "winnings": 0}
            
            # Player's turn - create view with hit/stand buttons
            view = BlackjackView(self, deck, player_hand, dealer_hand, bet_amount, hard_mode)
            
            await interaction.response.send_message(embed=embed, view=view)
            
            # Wait for game to finish
            await view.wait()
            
            return view.game_result
            
        except Exception as e:
            logger.error(f"Blackjack game error: {e}")
            return {"won": False, "winnings": 0, "error": str(e)}

class BlackjackView(discord.ui.View):
    def __init__(self, game: BlackjackGame, deck: List[Card], player_hand: List[Card], 
                 dealer_hand: List[Card], bet_amount: int, hard_mode: bool):
        super().__init__(timeout=120)
        self.game = game
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.bet_amount = bet_amount
        self.hard_mode = hard_mode
        self.game_result = {"won": False, "winnings": 0}
        
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🎯")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hit button - draw another card"""
        self.player_hand.append(self.deck.pop())
        
        # Check for bust
        if self.game.is_bust(self.player_hand):
            # Player busted
            embed = discord.Embed(
                title="🃏 Blackjack Game - BUST!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Your Hand",
                value=self.game.format_hand(self.player_hand, self.hard_mode),
                inline=False
            )
            embed.add_field(
                name="Dealer Hand",
                value=self.game.format_hand(self.dealer_hand, self.hard_mode),
                inline=False
            )
            embed.add_field(name="Result", value="💥 BUST! You lose!", inline=False)
            
            self.game_result = {"won": False, "winnings": 0}
            self.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            return
        
        # Update embed
        embed = discord.Embed(
            title="🃏 Blackjack Game",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Your Hand",
            value=self.game.format_hand(self.player_hand, self.hard_mode),
            inline=False
        )
        embed.add_field(
            name="Dealer Hand",
            value=f"{self.dealer_hand[0]} ?",
            inline=False
        )
        embed.add_field(
            name="Bet",
            value=f"{self.bet_amount:,} coins",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stand button - end player turn and play dealer"""
        await self.play_dealer_turn(interaction)
    
    async def play_dealer_turn(self, interaction: discord.Interaction):
        """Play out dealer's turn"""
        # Dealer draws until 17 or higher
        while self.game.get_best_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        
        # Determine winner
        player_value = self.game.get_best_value(self.player_hand)
        dealer_value = self.game.get_best_value(self.dealer_hand)
        dealer_bust = self.game.is_bust(self.dealer_hand)
        
        embed = discord.Embed(
            title="🃏 Blackjack Game - Final Result",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Your Hand",
            value=f"{self.game.format_hand(self.player_hand, self.hard_mode)} = {player_value}",
            inline=False
        )
        embed.add_field(
            name="Dealer Hand",
            value=f"{self.game.format_hand(self.dealer_hand, self.hard_mode)} = {dealer_value}",
            inline=False
        )
        
        if dealer_bust:
            embed.add_field(name="Result", value=f"🎉 Dealer busts! You win {self.bet_amount:,} coins!", inline=False)
            embed.color = discord.Color.green()
            self.game_result = {"won": True, "winnings": self.bet_amount}
        elif player_value > dealer_value:
            embed.add_field(name="Result", value=f"🎉 You win {self.bet_amount:,} coins!", inline=False)
            embed.color = discord.Color.green()
            self.game_result = {"won": True, "winnings": self.bet_amount}
        elif player_value < dealer_value:
            embed.add_field(name="Result", value="💥 Dealer wins! You lose!", inline=False)
            embed.color = discord.Color.red()
            self.game_result = {"won": False, "winnings": 0}
        else:
            embed.add_field(name="Result", value="🤝 Push! It's a tie!", inline=False)
            embed.color = discord.Color.orange()
            self.game_result = {"won": False, "winnings": 0, "push": True}
        
        self.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    def disable_all_items(self):
        """Disable all buttons"""
        for item in self.children:
            item.disabled = True

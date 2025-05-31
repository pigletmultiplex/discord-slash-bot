"""
Poker game implementation with Texas Hold'em Bonus
"""
import discord
import random
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = self.get_rank_value()
        
    def get_rank_value(self) -> int:
        """Get numeric value for card rank"""
        rank_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
            '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        return rank_values[self.rank]
    
    def __str__(self) -> str:
        suit_symbols = {'Hearts': '♥️', 'Diamonds': '♦️', 'Clubs': '♣️', 'Spades': '♠️'}
        return f"{self.rank}{suit_symbols[self.suit]}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __lt__(self, other):
        return self.value < other.value

class PokerGame:
    def __init__(self):
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        # Payout tables
        self.ante_payouts = {
            HandRank.ROYAL_FLUSH: 100,
            HandRank.STRAIGHT_FLUSH: 50,
            HandRank.FOUR_OF_A_KIND: 20,
            HandRank.FULL_HOUSE: 7,
            HandRank.FLUSH: 5,
            HandRank.STRAIGHT: 4,
            HandRank.THREE_OF_A_KIND: 3,
            HandRank.TWO_PAIR: 2,
            HandRank.PAIR: 1,
            HandRank.HIGH_CARD: 1
        }
        
        self.bonus_payouts = {
            HandRank.ROYAL_FLUSH: 1000,
            HandRank.STRAIGHT_FLUSH: 200,
            HandRank.FOUR_OF_A_KIND: 30,
            HandRank.FULL_HOUSE: 8,
            HandRank.FLUSH: 6,
            HandRank.STRAIGHT: 5,
            HandRank.THREE_OF_A_KIND: 4,
            HandRank.TWO_PAIR: 3,
            HandRank.PAIR: 2
        }

    def get_ante_multiplier(self, rank: HandRank) -> float:
        """Return the payout multiplier for ante bet for a given hand rank"""
        return float(self.ante_payouts.get(rank, 1))

    def get_bonus_multiplier(self, rank: HandRank) -> float:
        """Return the payout multiplier for bonus bet for a given hand rank"""
        return float(self.bonus_payouts.get(rank, 0))

    def create_deck(self) -> List[Card]:
        """Create a shuffled deck of cards"""
        deck = []
        for suit in self.suits:
            for rank in self.ranks:
                deck.append(Card(suit, rank))
        random.shuffle(deck)
        return deck

    def evaluate_hand(self, cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """Evaluate a 5-card poker hand and return rank and tie-breaker values"""
        if len(cards) != 5:
            raise ValueError("Hand must contain exactly 5 cards")
        
        # Sort cards by value (highest first)
        sorted_cards = sorted(cards, key=lambda x: x.value, reverse=True)
        values = [card.value for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = False
        if values == [14, 5, 4, 3, 2]:  # A-5 straight (wheel)
            is_straight = True
            values = [5, 4, 3, 2, 1]  # Treat ace as 1 for this straight
        elif all(values[i] - values[i+1] == 1 for i in range(4)):
            is_straight = True
        
        # Count card values
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1
        
        # Sort counts by frequency, then by value
        counts = sorted(value_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        # Determine hand rank
        if is_straight and is_flush:
            if values == [14, 13, 12, 11, 10]:
                return HandRank.ROYAL_FLUSH, values
            else:
                return HandRank.STRAIGHT_FLUSH, values
        elif counts[0][1] == 4:
            return HandRank.FOUR_OF_A_KIND, [counts[0][0], counts[1][0]]
        elif counts[0][1] == 3 and counts[1][1] == 2:
            return HandRank.FULL_HOUSE, [counts[0][0], counts[1][0]]
        elif is_flush:
            return HandRank.FLUSH, values
        elif is_straight:
            return HandRank.STRAIGHT, values
        elif counts[0][1] == 3:
            return HandRank.THREE_OF_A_KIND, [counts[0][0], counts[1][0], counts[2][0]]
        elif counts[0][1] == 2 and counts[1][1] == 2:
            return HandRank.TWO_PAIR, [counts[0][0], counts[1][0], counts[2][0]]
        elif counts[0][1] == 2:
            return HandRank.PAIR, [counts[0][0], counts[1][0], counts[2][0], counts[3][0]]
        else:
            return HandRank.HIGH_CARD, values

    def get_best_hand(self, hole_cards: List[Card], community_cards: List[Card]) -> Tuple[List[Card], HandRank, List[int]]:
        """Find the best 5-card hand from 7 available cards"""
        all_cards = hole_cards + community_cards
        if len(all_cards) != 7:
            raise ValueError("Must have exactly 7 cards (2 hole + 5 community)")
        
        best_hand: List[Card] = []
        best_rank: HandRank = HandRank.HIGH_CARD
        best_values: List[int] = []
        
        # Generate all possible 5-card combinations
        from itertools import combinations
        for combo in combinations(all_cards, 5):
            rank, values = self.evaluate_hand(list(combo))
            
            if not best_hand or rank.value > best_rank.value or \
               (rank.value == best_rank.value and values > best_values):
                best_hand = list(combo)
                best_rank = rank
                best_values = values
        
        return best_hand, best_rank, best_values

    def format_hand_name(self, rank: HandRank, cards: List[Card] = None) -> str:
        """Format hand rank as readable string"""
        names = {
            HandRank.HIGH_CARD: "High Card",
            HandRank.PAIR: "Pair", 
            HandRank.TWO_PAIR: "Two Pair",
            HandRank.THREE_OF_A_KIND: "Three of a Kind",
            HandRank.STRAIGHT: "Straight",
            HandRank.FLUSH: "Flush",
            HandRank.FULL_HOUSE: "Full House",
            HandRank.FOUR_OF_A_KIND: "Four of a Kind",
            HandRank.STRAIGHT_FLUSH: "Straight Flush",
            HandRank.ROYAL_FLUSH: "Royal Flush"
        }
        return names[rank]

    def format_cards(self, cards: List[Card]) -> str:
        """Format cards for display"""
        return " ".join(str(card) for card in cards)

    async def play_game(self, interaction: discord.Interaction, ante_amount: int, 
                       bonus_amount: int = 0, all_in: bool = False) -> Dict[str, Any]:
        """Play a complete Texas Hold'em Bonus game"""
        try:
            deck = self.create_deck()
            
            # Deal initial cards
            player_hole = [deck.pop(), deck.pop()]
            dealer_hole = [deck.pop(), deck.pop()]
            
            # Create initial embed
            embed = discord.Embed(
                title="🃏 Texas Hold'em Bonus Poker",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Your Hole Cards",
                value=self.format_cards(player_hole),
                inline=False
            )
            embed.add_field(name="Ante Bet", value=f"{ante_amount:,} coins", inline=True)
            if bonus_amount > 0:
                embed.add_field(name="Bonus Bet", value=f"{bonus_amount:,} coins", inline=True)
            
            if all_in:
                # All-in mode: skip to final result with doubled payout
                embed.add_field(name="Mode", value="ALL-IN (2x Payout)", inline=True)
                
                # Deal all community cards
                community_cards = [deck.pop() for _ in range(5)]
                
                # Evaluate hands
                player_best, player_rank, player_values = self.get_best_hand(player_hole, community_cards)
                dealer_best, dealer_rank, dealer_values = self.get_best_hand(dealer_hole, community_cards)
                
                return await self._resolve_final_result(
                    interaction, embed, player_hole, dealer_hole, community_cards,
                    player_best, player_rank, dealer_best, dealer_rank,
                    ante_amount, bonus_amount, all_in=True
                )
            else:
                # Normal play with betting rounds
                view = PokerView(self, deck, player_hole, dealer_hole, ante_amount, bonus_amount)
                await interaction.response.send_message(embed=embed, view=view)
                
                # Wait for game to finish
                await view.wait()
                return view.game_result
            
        except Exception as e:
            logger.error(f"Poker game error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred", ephemeral=True)
            return {"won": False, "winnings": 0, "error": str(e)}

    async def _resolve_final_result(self, interaction, embed, player_hole, dealer_hole, 
                                  community_cards, player_best, player_rank, dealer_best, 
                                  dealer_rank, ante_amount, bonus_amount, all_in=False):
        """Resolve final poker result"""
        # Update embed with final results
        embed.title = "🃏 Texas Hold'em Bonus - Final Result"
        embed.clear_fields()
        
        embed.add_field(
            name="Your Hole Cards",
            value=self.format_cards(player_hole),
            inline=True
        )
        embed.add_field(
            name="Dealer Hole Cards", 
            value=self.format_cards(dealer_hole),
            inline=True
        )
        embed.add_field(name="‎", value="‎", inline=True)  # Spacer
        
        embed.add_field(
            name="Community Cards",
            value=self.format_cards(community_cards),
            inline=False
        )
        
        embed.add_field(
            name="Your Best Hand",
            value=f"{self.format_cards(player_best)}\n**{self.format_hand_name(player_rank)}**",
            inline=True
        )
        embed.add_field(
            name="Dealer Best Hand",
            value=f"{self.format_cards(dealer_best)}\n**{self.format_hand_name(dealer_rank)}**",
            inline=True
        )
        embed.add_field(name="‎", value="‎", inline=True)  # Spacer
        
        # Determine winner
        total_winnings = 0
        result_text = []
        
        # Ante bet result
        if player_rank.value > dealer_rank.value:
            ante_payout = self.ante_payouts.get(player_rank, 1)
            ante_winnings = ante_amount * ante_payout * (2 if all_in else 1)
            total_winnings += ante_winnings
            result_text.append(f"🎉 Ante: Won {ante_winnings:,} coins ({ante_payout}:1)")
            embed.color = discord.Color.green()
        elif player_rank.value == dealer_rank.value:
            result_text.append("🤝 Ante: Push (tie)")
            embed.color = discord.Color.orange()
        else:
            result_text.append("💥 Ante: Lost")
            embed.color = discord.Color.red()
        
        # Bonus bet result (independent of ante)
        if bonus_amount > 0:
            if player_rank in self.bonus_payouts:
                bonus_payout = self.bonus_payouts[player_rank]
                bonus_winnings = bonus_amount * bonus_payout * (2 if all_in else 1)
                total_winnings += bonus_winnings
                result_text.append(f"🎉 Bonus: Won {bonus_winnings:,} coins ({bonus_payout}:1)")
            else:
                result_text.append("💥 Bonus: Lost")
        
        embed.add_field(
            name="Results",
            value="\n".join(result_text),
            inline=False
        )
        
        if total_winnings > 0:
            embed.add_field(name="Total Winnings", value=f"{total_winnings:,} coins", inline=True)
        
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)
        
        return {
            "won": total_winnings > 0,
            "winnings": total_winnings,
            "player_hand": self.format_hand_name(player_rank),
            "dealer_hand": self.format_hand_name(dealer_rank)
        }

class PokerView(discord.ui.View):
    def __init__(self, game: PokerGame, deck: List[Card], player_hole: List[Card],
                 dealer_hole: List[Card], ante_amount: int, bonus_amount: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.game = game
        self.deck = deck
        self.player_hole = player_hole
        self.dealer_hole = dealer_hole
        self.ante_amount = ante_amount
        self.bonus_amount = bonus_amount
        self.community_cards = []
        self.total_bet = ante_amount
        self.round = 0  # 0=preflop, 1=flop, 2=turn, 3=river
        self.game_result = {"won": False, "winnings": 0}
        
    @discord.ui.button(label="Play (2x Ante)", style=discord.ButtonStyle.primary, emoji="▶️")
    async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Continue playing - bet 2x ante"""
        if self.round == 0:  # Pre-flop decision
            self.total_bet += self.ante_amount * 2
            await self._deal_flop(interaction)
        else:
            await self._continue_round(interaction)
    
    @discord.ui.button(label="Check", style=discord.ButtonStyle.secondary, emoji="✋")
    async def check_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Check this round"""
        await self._continue_round(interaction)
    
    @discord.ui.button(label="Bet (1x Ante)", style=discord.ButtonStyle.success, emoji="💰")
    async def bet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Bet 1x ante"""
        if self.round > 0:  # Can only bet after flop
            self.total_bet += self.ante_amount
            await self._continue_round(interaction)
    
    @discord.ui.button(label="Fold", style=discord.ButtonStyle.danger, emoji="❌")
    async def fold_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fold and lose ante bet"""
        embed = discord.Embed(
            title="🃏 Texas Hold'em Bonus - Folded",
            color=discord.Color.red()
        )
        embed.add_field(name="Result", value="You folded and lost your ante bet", inline=False)
        embed.add_field(name="Loss", value=f"{self.ante_amount:,} coins", inline=True)
        
        # Check bonus bet
        if self.bonus_amount > 0:
            # Evaluate player's hole cards + any community cards dealt
            if len(self.community_cards) >= 3:
                all_community = self.community_cards + [self.deck.pop() for _ in range(5 - len(self.community_cards))]
                _, player_rank, _ = self.game.get_best_hand(self.player_hole, all_community)
                
                if player_rank in self.game.bonus_payouts:
                    bonus_payout = self.game.bonus_payouts[player_rank]
                    bonus_winnings = self.bonus_amount * bonus_payout
                    embed.add_field(name="Bonus Win", value=f"🎉 {bonus_winnings:,} coins ({bonus_payout}:1)", inline=True)
                    self.game_result = {"won": True, "winnings": bonus_winnings - self.ante_amount}
                else:
                    embed.add_field(name="Bonus Loss", value=f"💥 {self.bonus_amount:,} coins", inline=True)
                    self.game_result = {"won": False, "winnings": 0}
            else:
                self.game_result = {"won": False, "winnings": 0}
        else:
            self.game_result = {"won": False, "winnings": 0}
        
        self.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    async def _deal_flop(self, interaction):
        """Deal the flop (3 community cards)"""
        self.community_cards = [self.deck.pop() for _ in range(3)]
        self.round = 1
        
        embed = discord.Embed(
            title="🃏 Texas Hold'em Bonus - The Flop",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Your Hole Cards",
            value=self.game.format_cards(self.player_hole),
            inline=False
        )
        embed.add_field(
            name="Community Cards",
            value=self.game.format_cards(self.community_cards),
            inline=False
        )
        embed.add_field(name="Total Bet", value=f"{self.total_bet:,} coins", inline=True)
        
        # Update buttons for post-flop play
        self.play_button.label = "Continue"
        self.bet_button.disabled = False
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def _continue_round(self, interaction):
        """Continue to next round or finish game"""
        if self.round == 1:  # After flop, deal turn
            self.community_cards.append(self.deck.pop())
            self.round = 2
            title = "🃏 Texas Hold'em Bonus - The Turn"
        elif self.round == 2:  # After turn, deal river
            self.community_cards.append(self.deck.pop())
            self.round = 3
            title = "🃏 Texas Hold'em Bonus - The River"
        else:  # After river, show final result
            await self._show_final_result(interaction)
            return
        
        embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.add_field(
            name="Your Hole Cards",
            value=self.game.format_cards(self.player_hole),
            inline=False
        )
        embed.add_field(
            name="Community Cards",
            value=self.game.format_cards(self.community_cards),
            inline=False
        )
        embed.add_field(name="Total Bet", value=f"{self.total_bet:,} coins", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def _show_final_result(self, interaction):
        """Show final game result"""
        # Evaluate final hands
        player_best, player_rank, player_values = self.game.get_best_hand(self.player_hole, self.community_cards)
        dealer_best, dealer_rank, dealer_values = self.game.get_best_hand(self.dealer_hole, self.community_cards)
        
        result = await self.game._resolve_final_result(
            interaction, discord.Embed(), self.player_hole, self.dealer_hole,
            self.community_cards, player_best, player_rank, dealer_best, dealer_rank,
            self.ante_amount, self.bonus_amount
        )
        
        self.game_result = result
        self.disable_all_items()
        self.stop()
    
    def disable_all_items(self):
        """Disable all buttons"""
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = True
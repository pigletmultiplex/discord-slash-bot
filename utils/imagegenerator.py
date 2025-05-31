"""
Image generation utilities for Discord gambling bot
"""
from PIL import Image, ImageDraw, ImageFont
import io
import os
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SlotMachineImageGenerator:
    def __init__(self):
        # Slot machine dimensions
        self.reel_width = 120
        self.reel_height = 120
        self.spacing = 10
        self.machine_padding = 30
        
        # Colors
        self.background_color = (20, 25, 40)  # Dark blue
        self.reel_background = (45, 50, 65)   # Lighter blue
        self.border_color = (200, 180, 50)    # Gold
        self.text_color = (255, 255, 255)     # White
        
        # Symbol colors and representations
        self.symbol_styles = {
            '💎': {'color': (100, 200, 255), 'text': '💎'},  # Diamond - Blue
            '🔔': {'color': (255, 215, 0), 'text': '🔔'},    # Bell - Gold
            '🍇': {'color': (128, 0, 128), 'text': '🍇'},    # Grapes - Purple
            '🍊': {'color': (255, 165, 0), 'text': '🍊'},    # Orange - Orange
            '🍋': {'color': (255, 255, 0), 'text': '🍋'},    # Lemon - Yellow
            '🍒': {'color': (220, 20, 60), 'text': '🍒'},    # Cherry - Red
            '🔴': {'color': (255, 0, 0), 'text': '🔴'},      # Red Circle - Red
            '🟡': {'color': (255, 255, 0), 'text': '🟡'},    # Yellow Circle - Yellow
        }
        
    def create_slot_machine_image(self, reels: List[str], winnings: int = 0, 
                                 bet_amount: int = 0) -> io.BytesIO:
        """Create a slot machine image with the given reel results"""
        try:
            # Calculate total image dimensions
            total_width = (self.reel_width * 5) + (self.spacing * 4) + (self.machine_padding * 2)
            total_height = self.reel_height + (self.machine_padding * 2) + 100  # Extra space for text
            
            # Create image
            image = Image.new('RGB', (total_width, total_height), self.background_color)
            draw = ImageDraw.Draw(image)
            
            # Draw machine frame
            frame_rect = [
                self.machine_padding - 10,
                self.machine_padding - 10,
                total_width - self.machine_padding + 10,
                self.reel_height + self.machine_padding + 10
            ]
            draw.rectangle(frame_rect, outline=self.border_color, width=5)
            
            # Draw title
            try:
                title_font = ImageFont.truetype("arial.ttf", 24)
            except:
                title_font = ImageFont.load_default()
            
            title_text = "🎰 SLOT MACHINE 🎰"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (total_width - title_width) // 2
            draw.text((title_x, 5), title_text, fill=self.border_color, font=title_font)
            
            # Draw reels
            for i, symbol in enumerate(reels):
                x = self.machine_padding + (i * (self.reel_width + self.spacing))
                y = self.machine_padding
                
                # Draw reel background
                reel_rect = [x, y, x + self.reel_width, y + self.reel_height]
                draw.rectangle(reel_rect, fill=self.reel_background, outline=self.border_color, width=2)
                
                # Draw symbol
                self._draw_symbol(draw, symbol, x, y)
            
            # Draw result text
            result_y = self.reel_height + self.machine_padding + 20
            
            try:
                result_font = ImageFont.truetype("arial.ttf", 18)
            except:
                result_font = ImageFont.load_default()
            
            if winnings > 0:
                result_text = f"🎉 WIN! +{winnings:,} coins"
                result_color = (0, 255, 0)  # Green
            else:
                result_text = f"💥 No win this time"
                result_color = (255, 100, 100)  # Light red
            
            result_bbox = draw.textbbox((0, 0), result_text, font=result_font)
            result_width = result_bbox[2] - result_bbox[0]
            result_x = (total_width - result_width) // 2
            draw.text((result_x, result_y), result_text, fill=result_color, font=result_font)
            
            # Draw bet amount
            bet_text = f"Bet: {bet_amount:,} coins"
            bet_bbox = draw.textbbox((0, 0), bet_text, font=result_font)
            bet_width = bet_bbox[2] - bet_bbox[0]
            bet_x = (total_width - bet_width) // 2
            draw.text((bet_x, result_y + 25), bet_text, fill=self.text_color, font=result_font)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            logger.error(f"Error creating slot machine image: {e}")
            return self._create_fallback_image()
    
    def _draw_symbol(self, draw: ImageDraw.Draw, symbol: str, x: int, y: int):
        """Draw a symbol in the reel"""
        try:
            # Get symbol style
            style = self.symbol_styles.get(symbol, {'color': self.text_color, 'text': symbol})
            
            # Calculate center position
            center_x = x + self.reel_width // 2
            center_y = y + self.reel_height // 2
            
            # Draw symbol background circle
            circle_radius = 40
            circle_bbox = [
                center_x - circle_radius,
                center_y - circle_radius,
                center_x + circle_radius,
                center_y + circle_radius
            ]
            draw.ellipse(circle_bbox, fill=style['color'], outline=self.border_color, width=2)
            
            # Draw symbol text
            try:
                symbol_font = ImageFont.truetype("arial.ttf", 36)
            except:
                symbol_font = ImageFont.load_default()
            
            # Get text dimensions for centering
            text_bbox = draw.textbbox((0, 0), style['text'], font=symbol_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            text_x = center_x - text_width // 2
            text_y = center_y - text_height // 2
            
            # Draw text with outline for better visibility
            outline_color = (0, 0, 0)
            for adj in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                draw.text((text_x + adj[0], text_y + adj[1]), style['text'], 
                         fill=outline_color, font=symbol_font)
            
            draw.text((text_x, text_y), style['text'], fill=(255, 255, 255), font=symbol_font)
            
        except Exception as e:
            logger.error(f"Error drawing symbol {symbol}: {e}")
            # Fallback: draw simple text
            draw.text((x + 50, y + 50), symbol, fill=self.text_color)
    
    def _create_fallback_image(self) -> io.BytesIO:
        """Create a simple fallback image if main generation fails"""
        try:
            image = Image.new('RGB', (400, 200), self.background_color)
            draw = ImageDraw.Draw(image)
            
            text = "🎰 Slot Machine Result 🎰"
            draw.text((50, 90), text, fill=self.text_color)
            
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
        except:
            # If even fallback fails, return empty bytes
            return io.BytesIO()

class CardImageGenerator:
    def __init__(self):
        self.card_width = 80
        self.card_height = 120
        self.spacing = 10
        self.padding = 20
        
        # Card colors
        self.card_background = (255, 255, 255)  # White
        self.card_border = (0, 0, 0)            # Black
        self.red_color = (220, 20, 60)          # Red suits
        self.black_color = (0, 0, 0)            # Black suits
        
    def create_hand_image(self, cards: List[str], title: str = "Hand") -> io.BytesIO:
        """Create an image showing a hand of cards"""
        try:
            # Calculate dimensions
            total_width = (self.card_width * len(cards)) + (self.spacing * (len(cards) - 1)) + (self.padding * 2)
            total_height = self.card_height + (self.padding * 2) + 50  # Extra for title
            
            # Create image
            image = Image.new('RGB', (total_width, total_height), (20, 25, 40))
            draw = ImageDraw.Draw(image)
            
            # Draw title
            try:
                title_font = ImageFont.truetype("arial.ttf", 20)
            except:
                title_font = ImageFont.load_default()
            
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (total_width - title_width) // 2
            draw.text((title_x, 5), title, fill=(255, 255, 255), font=title_font)
            
            # Draw cards
            for i, card_str in enumerate(cards):
                x = self.padding + (i * (self.card_width + self.spacing))
                y = self.padding + 30
                
                self._draw_card(draw, card_str, x, y)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            logger.error(f"Error creating card image: {e}")
            return io.BytesIO()
    
    def _draw_card(self, draw: ImageDraw.Draw, card_str: str, x: int, y: int):
        """Draw a single card"""
        try:
            # Draw card background
            card_rect = [x, y, x + self.card_width, y + self.card_height]
            draw.rectangle(card_rect, fill=self.card_background, outline=self.card_border, width=2)
            
            # Parse card (assumes format like "A♠" or "10♥")
            if len(card_str) >= 2:
                rank = card_str[:-1]
                suit = card_str[-1]
                
                # Determine color
                color = self.red_color if suit in ['♥', '♦'] else self.black_color
                
                # Draw rank in corners
                try:
                    rank_font = ImageFont.truetype("arial.ttf", 16)
                except:
                    rank_font = ImageFont.load_default()
                
                draw.text((x + 5, y + 5), rank, fill=color, font=rank_font)
                
                # Draw suit in center
                try:
                    suit_font = ImageFont.truetype("arial.ttf", 24)
                except:
                    suit_font = ImageFont.load_default()
                
                suit_bbox = draw.textbbox((0, 0), suit, font=suit_font)
                suit_width = suit_bbox[2] - suit_bbox[0]
                suit_height = suit_bbox[3] - suit_bbox[1]
                
                suit_x = x + (self.card_width - suit_width) // 2
                suit_y = y + (self.card_height - suit_height) // 2
                
                draw.text((suit_x, suit_y), suit, fill=color, font=suit_font)
                
        except Exception as e:
            logger.error(f"Error drawing card {card_str}: {e}")
            # Fallback: draw card string as text
            draw.text((x + 10, y + 50), card_str, fill=self.black_color)

class ProfileBadgeGenerator:
    def __init__(self):
        self.badge_size = 80
        self.badge_spacing = 10
        self.padding = 20
        self.max_badges_per_row = 6
        
        # Colors
        self.background_color = (30, 35, 50)     # Dark blue
        self.card_background = (45, 50, 65)      # Card background
        self.text_color = (255, 255, 255)        # White text
        self.accent_color = (255, 215, 0)        # Gold accent
        self.progress_bg = (60, 65, 80)          # Progress bar background
        self.progress_fill = (100, 200, 100)     # Progress bar fill
        
        # Badge tier colors
        self.tier_colors = {
            'bronze': (205, 127, 50),
            'silver': (192, 192, 192),
            'gold': (255, 215, 0),
            'platinum': (229, 228, 226),
            'diamond': (185, 242, 255)
        }
    
    def create_profile_badge(self, user_data: Dict[str, Any], achievements: List[Any], 
                           progress: Dict[str, Dict[str, Any]]) -> io.BytesIO:
        """Create a profile badge image showing achievements and progress"""
        try:
            # Calculate dimensions
            num_achievements = len(achievements)
            rows = (num_achievements + self.max_badges_per_row - 1) // self.max_badges_per_row
            
            # Account for progress bars below badges
            total_width = (self.badge_size * min(self.max_badges_per_row, num_achievements)) + \
                         (self.badge_spacing * (min(self.max_badges_per_row, num_achievements) - 1)) + \
                         (self.padding * 2)
            total_height = (self.badge_size * rows) + (self.badge_spacing * (rows - 1)) + \
                          (self.padding * 2) + 200  # Extra space for stats and title
            
            # Ensure minimum width
            total_width = max(total_width, 600)
            
            # Create image
            image = Image.new('RGB', (total_width, total_height), self.background_color)
            draw = ImageDraw.Draw(image)
            
            # Draw title
            try:
                title_font = ImageFont.truetype("arial.ttf", 24)
                subtitle_font = ImageFont.truetype("arial.ttf", 16)
                badge_font = ImageFont.truetype("arial.ttf", 12)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                badge_font = ImageFont.load_default()
            
            title_text = f"🏆 Player Profile Badges"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (total_width - title_width) // 2
            draw.text((title_x, 10), title_text, fill=self.accent_color, font=title_font)
            
            # Draw player stats
            balance = user_data.get('balance', 0)
            games_played = user_data.get('games_played', 0)
            win_rate = (user_data.get('games_won', 0) / games_played * 100) if games_played > 0 else 0
            
            stats_text = f"Balance: {balance:,} coins | Games: {games_played} | Win Rate: {win_rate:.1f}%"
            stats_bbox = draw.textbbox((0, 0), stats_text, font=subtitle_font)
            stats_width = stats_bbox[2] - stats_bbox[0]
            stats_x = (total_width - stats_width) // 2
            draw.text((stats_x, 45), stats_text, fill=self.text_color, font=subtitle_font)
            
            # Draw achievements section header
            achievements_header = f"Achievements Earned: {len(achievements)}"
            header_bbox = draw.textbbox((0, 0), achievements_header, font=subtitle_font)
            header_width = header_bbox[2] - header_bbox[0]
            header_x = (total_width - header_width) // 2
            draw.text((header_x, 80), achievements_header, fill=self.text_color, font=subtitle_font)
            
            # Draw achievement badges
            start_y = 120
            for i, achievement in enumerate(achievements):
                row = i // self.max_badges_per_row
                col = i % self.max_badges_per_row
                
                # Calculate position
                badges_in_row = min(self.max_badges_per_row, len(achievements) - row * self.max_badges_per_row)
                row_width = (self.badge_size * badges_in_row) + (self.badge_spacing * (badges_in_row - 1))
                start_x = (total_width - row_width) // 2
                
                x = start_x + (col * (self.badge_size + self.badge_spacing))
                y = start_y + (row * (self.badge_size + self.badge_spacing + 30))
                
                self._draw_achievement_badge(draw, achievement, x, y, badge_font)
            
            # Draw progress section
            progress_y = start_y + (rows * (self.badge_size + self.badge_spacing + 30)) + 40
            
            # Show top 3 achievements closest to completion
            closest_achievements = self._get_closest_achievements(progress, 3)
            if closest_achievements:
                progress_header = "Closest to Unlock:"
                progress_bbox = draw.textbbox((0, 0), progress_header, font=subtitle_font)
                progress_width = progress_bbox[2] - progress_bbox[0]
                progress_x = (total_width - progress_width) // 2
                draw.text((progress_x, progress_y), progress_header, fill=self.text_color, font=subtitle_font)
                
                # Draw progress bars
                for i, (achievement_id, prog_data) in enumerate(closest_achievements):
                    y_pos = progress_y + 30 + (i * 35)
                    self._draw_progress_bar(draw, achievement_id, prog_data, 50, y_pos, 
                                          total_width - 100, badge_font)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            logger.error(f"Error creating profile badge: {e}")
            return self._create_fallback_profile_image()
    
    def _draw_achievement_badge(self, draw: ImageDraw.Draw, achievement: Any, 
                              x: int, y: int, font):
        """Draw a single achievement badge"""
        try:
            # Draw badge background circle
            badge_rect = [x, y, x + self.badge_size, y + self.badge_size]
            
            # Determine tier color based on XP reward
            if achievement.xp_reward >= 500:
                color = self.tier_colors['diamond']
            elif achievement.xp_reward >= 300:
                color = self.tier_colors['platinum']
            elif achievement.xp_reward >= 200:
                color = self.tier_colors['gold']
            elif achievement.xp_reward >= 100:
                color = self.tier_colors['silver']
            else:
                color = self.tier_colors['bronze']
            
            # Draw badge circle
            circle_center = (x + self.badge_size // 2, y + self.badge_size // 2)
            circle_radius = self.badge_size // 2 - 2
            circle_bbox = [
                circle_center[0] - circle_radius,
                circle_center[1] - circle_radius,
                circle_center[0] + circle_radius,
                circle_center[1] + circle_radius
            ]
            draw.ellipse(circle_bbox, fill=color, outline=self.accent_color, width=2)
            
            # Draw achievement icon
            icon_text = achievement.icon
            try:
                icon_font = ImageFont.truetype("arial.ttf", 24)
            except:
                icon_font = font
            
            icon_bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
            icon_width = icon_bbox[2] - icon_bbox[0]
            icon_height = icon_bbox[3] - icon_bbox[1]
            
            icon_x = circle_center[0] - icon_width // 2
            icon_y = circle_center[1] - icon_height // 2
            
            draw.text((icon_x, icon_y), icon_text, fill=(255, 255, 255), font=icon_font)
            
            # Draw achievement name below badge
            name_bbox = draw.textbbox((0, 0), achievement.name, font=font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = x + (self.badge_size - name_width) // 2
            name_y = y + self.badge_size + 5
            
            draw.text((name_x, name_y), achievement.name, fill=self.text_color, font=font)
            
        except Exception as e:
            logger.error(f"Error drawing achievement badge: {e}")
            # Fallback: draw simple rectangle
            draw.rectangle([x, y, x + self.badge_size, y + self.badge_size], 
                         fill=self.tier_colors['bronze'], outline=self.accent_color)
            draw.text((x + 10, y + 30), "?", fill=self.text_color, font=font)
    
    def _draw_progress_bar(self, draw: ImageDraw.Draw, achievement_id: str, 
                          progress_data: Dict[str, Any], x: int, y: int, 
                          width: int, font):
        """Draw a progress bar for an achievement"""
        try:
            # Get achievement name (simplified from ID)
            achievement_name = achievement_id.replace('_', ' ').title()
            current = progress_data['current']
            target = progress_data['target']
            percentage = progress_data['percentage']
            
            # Draw progress text
            progress_text = f"{achievement_name}: {current}/{target} ({percentage:.0f}%)"
            draw.text((x, y), progress_text, fill=self.text_color, font=font)
            
            # Draw progress bar background
            bar_y = y + 15
            bar_height = 8
            bar_rect = [x, bar_y, x + width, bar_y + bar_height]
            draw.rectangle(bar_rect, fill=self.progress_bg, outline=self.text_color)
            
            # Draw progress fill
            fill_width = int(width * (percentage / 100))
            if fill_width > 0:
                fill_rect = [x, bar_y, x + fill_width, bar_y + bar_height]
                draw.rectangle(fill_rect, fill=self.progress_fill)
            
        except Exception as e:
            logger.error(f"Error drawing progress bar: {e}")
    
    def _get_closest_achievements(self, progress: Dict[str, Dict[str, Any]], 
                                count: int) -> List[Tuple[str, Dict[str, Any]]]:
        """Get achievements closest to completion"""
        incomplete = [(aid, prog) for aid, prog in progress.items() 
                     if not prog['completed'] and prog['percentage'] > 0]
        
        # Sort by percentage descending
        incomplete.sort(key=lambda x: x[1]['percentage'], reverse=True)
        
        return incomplete[:count]
    
    def _create_fallback_profile_image(self) -> io.BytesIO:
        """Create a simple fallback profile image"""
        try:
            image = Image.new('RGB', (400, 200), self.background_color)
            draw = ImageDraw.Draw(image)
            
            text = "🏆 Profile Badges 🏆"
            draw.text((100, 90), text, fill=self.text_color)
            
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
        except:
            return io.BytesIO()
"""
Main entry point for the Discord Gambling Bot
"""
import asyncio
import logging
import os
from bot import GamblingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        # Get Discord token from environment variables
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error("DISCORD_TOKEN environment variable not found!")
            return
        
        # Create and start the bot
        bot = GamblingBot()
        logger.info("Starting Discord Gambling Bot...")
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        logger.info("Bot has been shut down")

if __name__ == "__main__":
    asyncio.run(main())

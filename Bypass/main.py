import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, PREMIUM_USERS, ADMIN_IDS, USER_STATS
from commands import router
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load premium users from environment or file
premium_data = os.getenv("PREMIUM_USERS_JSON")
if premium_data:
    try:
        loaded = json.loads(premium_data)
        PREMIUM_USERS.update({int(k): v for k, v in loaded.items()})
        logger.info(f"Loaded {len(PREMIUM_USERS)} premium users from env")
    except Exception as e:
        logger.error(f"Error loading premium users from env: {e}")
elif os.path.exists('/root/3D/premium_users.json'):
    try:
        with open('/root/3D/premium_users.json', 'r') as f:
            loaded = json.load(f)
            PREMIUM_USERS.update({int(k): v for k, v in loaded.items()})
        logger.info(f"Loaded {len(PREMIUM_USERS)} premium users from file")
    except Exception as e:
        logger.error(f"Error loading premium users from file: {e}")

# Load admin IDs from file
if os.path.exists('/root/3D/admin_ids.json'):
    try:
        with open('/root/3D/admin_ids.json', 'r') as f:
            loaded = json.load(f)
            ADMIN_IDS.extend(loaded)
        logger.info(f"Loaded {len(ADMIN_IDS)} admin users")
    except Exception as e:
        logger.error(f"Error loading admin IDs: {e}")

# Load user stats from file
if os.path.exists('/root/3D/user_stats.json'):
    try:
        with open('/root/3D/user_stats.json', 'r') as f:
            loaded = json.load(f)
            USER_STATS.update({int(k): v for k, v in loaded.items()})
        logger.info(f"Loaded stats for {len(USER_STATS)} users")
    except Exception as e:
        logger.error(f"Error loading user stats: {e}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    """Main entry point for the bot."""
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
    finally:
        # Properly close all sessions
        try:
            from functions.charge_functions import _session as charge_session
            if charge_session and not charge_session.closed:
                await charge_session.close()
                logger.info("Charge session closed")
        except Exception as e:
            logger.error(f"Error closing charge session: {e}")
        
        try:
            from commands.co import _session as co_session
            if co_session and not co_session.closed:
                await co_session.close()
                logger.info("CO session closed")
        except Exception as e:
            logger.error(f"Error closing CO session: {e}")
        
        await bot.session.close()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())

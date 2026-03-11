import logging
from aiogram import Router

# Configure logging
logger = logging.getLogger(__name__)

router = Router()

# Import routers with error handling
try:
    from commands.start import router as start_router
    router.include_router(start_router)
    logger.info("Loaded start router")
except Exception as e:
    logger.error(f"Failed to load start router: {e}", exc_info=True)

try:
    from commands.co import router as co_router
    router.include_router(co_router)
    logger.info("Loaded co router")
except Exception as e:
    logger.error(f"Failed to load co router: {e}", exc_info=True)

try:
    from commands.gen import router as gen_router
    router.include_router(gen_router)
    logger.info("Loaded gen router")
except Exception as e:
    logger.error(f"Failed to load gen router: {e}", exc_info=True)

try:
    from commands.admin import router as admin_router
    router.include_router(admin_router)
    logger.info("Loaded admin router")
except Exception as e:
    logger.error(f"Failed to load admin router: {e}", exc_info=True)

# Export router for use in main.py
__all__ = ['router']

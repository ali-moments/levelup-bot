"""Main entry point for LevelUp Bot."""

import asyncio
import logging
import sys

# Apply CPU patches BEFORE importing anything that uses ONNX
from .ocr.cpu_patch import apply_cpu_patches
apply_cpu_patches()

from .bot import Bot

logger = logging.getLogger(__name__)


async def main():
    """Main async function."""
    # Print initial startup message
    print("\n" + "=" * 60)
    print("🤖 LevelUp Bot")
    print("=" * 60)
    print("Initializing...\n")
    
    # Create and initialize bot
    bot = Bot()
    
    # Initialize all components
    if not await bot.initialize():
        logger.error("❌ Bot initialization failed")
        return
    
    # Start all services
    await bot.start()
    
    # Run until shutdown
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 Bot stopped by user")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error(f"❌ Fatal error: {e}")
        logger.error("=" * 60)
    
    # Force exit to ensure process terminates
    logger.info("Exiting process...")
    sys.exit(0)


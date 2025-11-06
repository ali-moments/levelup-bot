"""Bonus message sending service."""

import asyncio
import logging
import time
from telethon import TelegramClient
from telethon.tl.types import Channel

from ..config.settings import BONUS_MESSAGE, BONUS_INTERVAL
from ..telegram.messaging import send_bonus_message

logger = logging.getLogger(__name__)


async def bonus_message_loop(
    client: TelegramClient,
    group_entity: Channel,
    running_flag: asyncio.Event
):
    """Async loop that sends bonus messages every BONUS_INTERVAL seconds with precise timing.
    
    Args:
        client: Telegram client instance
        group_entity: Target group entity
        running_flag: Event flag to control loop lifecycle
    """
    # Send first bonus message immediately
    if running_flag.is_set():
        logger.info("Sending first bonus message immediately...")
        await send_bonus_message(client, group_entity, BONUS_MESSAGE)
        last_send_time = time.time()  # Track when message was actually sent
        logger.info(f"First bonus message sent. Next in {BONUS_INTERVAL} seconds...")
    
    # Then send every BONUS_INTERVAL seconds with precise timing
    while running_flag.is_set():
        try:
            # Calculate sleep time based on when message was actually sent
            current_time = time.time()
            time_since_last_send = current_time - last_send_time
            sleep_time = BONUS_INTERVAL - time_since_last_send
            
            # If we're already past the interval, send immediately
            if sleep_time <= 0:
                sleep_time = 0
            else:
                await asyncio.sleep(sleep_time)
            
            if running_flag.is_set():
                logger.info(f"Sending bonus message (every {BONUS_INTERVAL}s = 3 minutes + 1 second)...")
                await send_bonus_message(client, group_entity, BONUS_MESSAGE)
                last_send_time = time.time()  # Update last send time to actual send completion
                logger.info(f"Bonus message sent. Next in {BONUS_INTERVAL} seconds...")
        except asyncio.CancelledError:
            logger.info("Bonus message loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in bonus message loop: {e}")
            if running_flag.is_set():
                await asyncio.sleep(5)


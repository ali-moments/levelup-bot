"""Bonus message sending service."""

import asyncio
import logging
import time
import random
import secrets
import os
import hashlib
from telethon import TelegramClient
from telethon.tl.types import Channel

from ..config.settings import BONUS_MESSAGE, BONUS_INTERVAL_MIN, BONUS_INTERVAL_MAX
from ..telegram.messaging import send_bonus_message

logger = logging.getLogger(__name__)


def _get_random_seed():
    """Generate a strong random seed using multiple entropy sources.
    
    Uses time, process ID, and cryptographically secure random data to create
    a seed that's hard to predict, helping avoid bot detection patterns.
    
    Returns:
        int: A seed value for random number generation
    """
    # Combine multiple entropy sources for maximum unpredictability
    time_ns = time.time_ns()  # Nanosecond precision timestamp
    pid = os.getpid()  # Process ID (unique per process)
    # Use cryptographically secure random bytes for additional entropy
    crypto_random = secrets.token_bytes(16)  # 128 bits of secure randomness
    
    # Use hash of combined values to mix all entropy sources
    seed_data = f"{time_ns}_{pid}_{crypto_random.hex()}"
    seed_hash = int(hashlib.sha256(seed_data.encode()).hexdigest()[:16], 16)
    return seed_hash


def _get_random_interval():
    """Get a random interval between MIN and MAX seconds.
    
    Uses a fresh seed each time to ensure good randomization
    and avoid predictable patterns.
    
    Returns:
        float: Random interval in seconds
    """
    # Re-seed with fresh entropy for each call
    random.seed(_get_random_seed())
    interval = random.uniform(BONUS_INTERVAL_MIN, BONUS_INTERVAL_MAX)
    return round(interval, 2)  # Round to 2 decimal places


async def bonus_message_loop(
    client: TelegramClient,
    group_entity: Channel,
    running_flag: asyncio.Event
):
    """Async loop that sends bonus messages with random intervals between MIN and MAX seconds.
    
    Uses cryptographically strong randomization to avoid detection patterns.
    
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
        
        # Get first random interval
        next_interval = _get_random_interval()
        logger.info(f"First bonus message sent. Next in {next_interval:.2f} seconds (random: {BONUS_INTERVAL_MIN}-{BONUS_INTERVAL_MAX}s)...")
    
    # Then send with random intervals between MIN and MAX
    while running_flag.is_set():
        try:
            # Get a new random interval for this cycle
            next_interval = _get_random_interval()
            
            # Calculate sleep time based on when message was actually sent
            current_time = time.time()
            time_since_last_send = current_time - last_send_time
            sleep_time = next_interval - time_since_last_send
            
            # If we're already past the interval, send immediately
            if sleep_time <= 0:
                sleep_time = 0
            else:
                logger.info(f"Waiting {sleep_time:.2f} seconds before next bonus message...")
                await asyncio.sleep(sleep_time)
            
            if running_flag.is_set():
                logger.info(f"Sending bonus message (interval: {next_interval:.2f}s, range: {BONUS_INTERVAL_MIN}-{BONUS_INTERVAL_MAX}s)...")
                await send_bonus_message(client, group_entity, BONUS_MESSAGE)
                last_send_time = time.time()  # Update last send time to actual send completion
                
                # Get next random interval for the following cycle
                next_interval = _get_random_interval()
                logger.info(f"Bonus message sent. Next in {next_interval:.2f} seconds (random: {BONUS_INTERVAL_MIN}-{BONUS_INTERVAL_MAX}s)...")
        except asyncio.CancelledError:
            logger.info("Bonus message loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in bonus message loop: {e}")
            if running_flag.is_set():
                await asyncio.sleep(5)


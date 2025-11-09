"""Word sending service."""

import asyncio
import logging
import queue
import random
from typing import List

from ..config.settings import ENABLE_WORD_SENDING, MIN_MESSAGE_DELAY, MAX_MESSAGE_DELAY

logger = logging.getLogger(__name__)


async def word_sender_loop(
    wordlist: List[str],
    message_queue: queue.Queue,
    running_flag: asyncio.Event
):
    """Main loop that sends random words to the group.
    
    Args:
        wordlist: List of words to send
        message_queue: Queue to add messages to
        running_flag: Event flag to control loop lifecycle
    """
    if not ENABLE_WORD_SENDING:
        logger.info("Word sending is disabled. Exiting main loop.")
        return
    
    if not wordlist:
        logger.error("Wordlist is empty. Cannot send messages.")
        return
    
    # Calculate messages per hour for logging
    from ..config.settings import WORD_SENDER_SLOW_MODE
    if WORD_SENDER_SLOW_MODE:
        rate_info = "100-150 messages/hour"
    else:
        rate_info = "900-1100 messages/hour"
    
    logger.info(f"Starting main message loop ({MIN_MESSAGE_DELAY}-{MAX_MESSAGE_DELAY}s delay = {rate_info})...")
    
    while running_flag.is_set():
        try:
            # Select random word
            word = random.choice(wordlist)
            
            # Add message to queue
            message_queue.put({
                'type': 'word',
                'message': word
            })
            
            logger.info(f"Queued word: {word}")
            
            # Random delay between MIN and MAX
            delay = random.uniform(MIN_MESSAGE_DELAY, MAX_MESSAGE_DELAY)
            await asyncio.sleep(delay)
            
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)


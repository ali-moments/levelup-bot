"""Message queue worker thread."""

import asyncio
import logging
import queue
import random
import threading
import time
from typing import Optional

from ..config.settings import MIN_MESSAGE_DELAY, MAX_MESSAGE_DELAY
from ..telegram.messaging import send_message_to_group
from telethon import TelegramClient
from telethon.tl.types import Channel

logger = logging.getLogger(__name__)


def message_worker(
    message_queue: queue.Queue,
    client: TelegramClient,
    group_entity: Channel,
    event_loop: asyncio.AbstractEventLoop,
    running_flag: threading.Event
):
    """Worker thread that processes messages from the queue.
    
    Args:
        message_queue: Queue containing messages to send
        client: Telegram client instance
        group_entity: Target group entity
        event_loop: Async event loop
        running_flag: Event flag to control worker lifecycle
    """
    while running_flag.is_set():
        try:
            # Wait for event loop to be available
            if not event_loop:
                time.sleep(0.5)
                continue
            
            # Get message from queue (with timeout to check running flag)
            try:
                message_data = message_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            if message_data is None:  # Shutdown signal
                break
            
            message_type = message_data.get('type')
            
            if message_type == 'word':
                # Send word message
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        send_message_to_group(client, group_entity, message_data['message']),
                        event_loop
                    )
                    future.result(timeout=10)  # Wait up to 10 seconds
                except Exception as e:
                    logger.error(f"Error sending word message: {e}")
                
                # Random delay between MIN and MAX to achieve target messages/hour
                # Check running flag during sleep to exit quickly
                delay = random.uniform(MIN_MESSAGE_DELAY, MAX_MESSAGE_DELAY)
                elapsed = 0
                while elapsed < delay and running_flag.is_set():
                    sleep_chunk = min(0.5, delay - elapsed)  # Check every 0.5 seconds
                    time.sleep(sleep_chunk)
                    elapsed += sleep_chunk
                
            message_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error in message worker: {e}")
            time.sleep(5)


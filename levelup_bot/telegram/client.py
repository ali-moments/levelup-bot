"""Telegram client initialization and connection management."""

import logging
from typing import Optional
from telethon import TelegramClient

from ..config.settings import API_ID, API_HASH, SESSION_NAME

logger = logging.getLogger(__name__)


async def initialize_client() -> Optional[TelegramClient]:
    """Initialize and connect Telegram client.
    
    Returns:
        TelegramClient instance if successful, None otherwise
    """
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        logger.info("Telegram client connected successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        return None

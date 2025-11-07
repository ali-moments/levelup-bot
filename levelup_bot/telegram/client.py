"""Telegram client initialization and connection management."""

import logging
import asyncio
from typing import Optional
from telethon import TelegramClient
from telethon.errors import PersistentTimestampOutdatedError

from ..config.settings import API_ID, API_HASH, SESSION_NAME

logger = logging.getLogger(__name__)


async def initialize_client() -> Optional[TelegramClient]:
    """Initialize and connect Telegram client.
    
    Handles PersistentTimestampOutdatedError by syncing the session state.
    
    Returns:
        TelegramClient instance if successful, None otherwise
    """
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        logger.info("Telegram client connected successfully")
        
        # Sync session state to fix PersistentTimestampOutdatedError
        logger.info("🔄 Syncing session state to prevent timestamp errors...")
        try:
            # Call get_dialogs to refresh session state
            await client.get_dialogs(limit=1)
            logger.info("✅ Session state synced successfully")
        except PersistentTimestampOutdatedError:
            logger.warning("⚠️  PersistentTimestampOutdatedError detected, attempting to catch up...")
            try:
                # Try to catch up the session
                await client.catch_up()
                logger.info("✅ Session caught up successfully")
            except Exception as catch_up_error:
                logger.warning(f"⚠️  Could not catch up session: {catch_up_error}")
                logger.info("   This is usually harmless, continuing anyway...")
        except Exception as sync_error:
            logger.debug(f"Session sync warning (non-critical): {sync_error}")
        
        return client
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        return None

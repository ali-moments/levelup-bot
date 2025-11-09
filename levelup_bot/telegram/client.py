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
    print("=" * 60)
    print("[DEBUG] CLIENT INITIALIZATION STARTED")
    print(f"[DEBUG] Session: {SESSION_NAME}")
    print(f"[DEBUG] API_ID: {API_ID}")
    print("=" * 60)
    
    try:
        print("[DEBUG] Creating TelegramClient instance...")
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        print("[DEBUG] Starting client connection...")
        await client.start()
        
        # Verify connection status
        is_connected = client.is_connected()
        print(f"[DEBUG] Client started. Connected: {is_connected}")
        logger.info("Telegram client connected successfully")
        
        if not is_connected:
            print("[DEBUG] ⚠️  WARNING: Client reports not connected!")
            logger.warning("Client reports not connected after start()")
        
        # Sync session state to fix PersistentTimestampOutdatedError
        print("[DEBUG] Syncing session state...")
        logger.info("🔄 Syncing session state to prevent timestamp errors...")
        try:
            # Call get_dialogs to refresh session state
            print("[DEBUG] Calling get_dialogs(limit=1) to refresh session...")
            await client.get_dialogs(limit=1)
            print("[DEBUG] ✅ Session state synced successfully")
            logger.info("✅ Session state synced successfully")
        except PersistentTimestampOutdatedError:
            print("[DEBUG] ⚠️  PersistentTimestampOutdatedError detected")
            logger.warning("⚠️  PersistentTimestampOutdatedError detected, attempting to catch up...")
            try:
                # Try to catch up the session
                print("[DEBUG] Attempting to catch up session...")
                await client.catch_up()
                print("[DEBUG] ✅ Session caught up successfully")
                logger.info("✅ Session caught up successfully")
            except Exception as catch_up_error:
                print(f"[DEBUG] ⚠️  Could not catch up session: {catch_up_error}")
                logger.warning(f"⚠️  Could not catch up session: {catch_up_error}")
                logger.info("   This is usually harmless, continuing anyway...")
        except Exception as sync_error:
            print(f"[DEBUG] Session sync warning (non-critical): {sync_error}")
            logger.debug(f"Session sync warning (non-critical): {sync_error}")
        
        # Final connection check
        final_connected = client.is_connected()
        print(f"[DEBUG] Final connection status: {final_connected}")
        print("[DEBUG] CLIENT INITIALIZATION COMPLETED")
        print("=" * 60)
        
        if final_connected:
            print("[DEBUG] ✅ Client is ready to receive messages")
        else:
            print("[DEBUG] ❌ WARNING: Client may not be ready to receive messages!")
        
        return client
    except Exception as e:
        print(f"[DEBUG] ❌ ERROR: Failed to initialize client: {e}")
        print("=" * 60)
        logger.error(f"Failed to initialize client: {e}")
        import traceback
        print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
        return None

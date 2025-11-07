"""Message sending functionality."""

import asyncio
import logging
from telethon import TelegramClient, errors
from telethon.tl.types import Channel

logger = logging.getLogger(__name__)


async def send_message_to_group(client: TelegramClient, group_entity: Channel, message: str):
    """Send a message to the group.
    
    Args:
        client: Telegram client instance
        group_entity: Target group/channel entity
        message: Message text to send
        
    Returns:
        Message object if successful, None otherwise
    """
    try:
        if not group_entity:
            logger.error("Group entity not set")
            return None
        
        sent_message = await client.send_message(group_entity, message)
        logger.info(f"Sent message to group: {message[:50]}...")
        return sent_message
    except errors.FloodWaitError as e:
        logger.warning(f"Rate limited. Waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        return None
    except Exception as e:
        logger.error(f"Error sending message to group: {e}")
        return None


async def send_bonus_message(client: TelegramClient, group_entity: Channel, bonus_message: str) -> bool:
    """Send bonus message to the group.
    
    Args:
        client: Telegram client instance
        group_entity: Target group/channel entity
        bonus_message: Bonus message text to send
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not group_entity:
            logger.error("Group entity not set")
            return False
        
        await client.send_message(group_entity, bonus_message)
        logger.info(f"Sent bonus message to group: {bonus_message}")
        return True
    except errors.FloodWaitError as e:
        logger.warning(f"Rate limited. Waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        logger.error(f"Error sending bonus message: {e}")
        return False


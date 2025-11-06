"""Group finding and joining functionality."""

import logging
from typing import Optional
from telethon import TelegramClient, errors
from telethon.tl.types import Channel

from ..config.settings import GROUP_NAME, GROUP_INVITE_URL

logger = logging.getLogger(__name__)


async def find_group_by_name(client: TelegramClient, group_name: str) -> Optional[Channel]:
    """Find a group by name from dialogs.
    
    Args:
        client: Telegram client instance
        group_name: Name of the group to find
        
    Returns:
        Channel entity if found, None otherwise
    """
    try:
        if not group_name:
            return None
        
        logger.info(f"Searching for group: '{group_name}' in dialogs...")
        async for dialog in client.iter_dialogs():
            if isinstance(dialog.entity, Channel) and not dialog.entity.broadcast:
                # Check if the title matches (case-insensitive)
                if dialog.entity.title.lower() == group_name.lower():
                    logger.info(f"Found group: {dialog.entity.title}")
                    return dialog.entity
        
        logger.warning(f"Group '{group_name}' not found in dialogs")
        return None
    except Exception as e:
        logger.error(f"Error finding group by name: {e}")
        return None


async def join_group_via_invite(client: TelegramClient, invite_url: str) -> Optional[Channel]:
    """Join a group using an invite link.
    
    Args:
        client: Telegram client instance
        invite_url: Invite URL or hash
        
    Returns:
        Channel entity if successful, None otherwise
    """
    try:
        if not invite_url:
            return None
        
        # Extract invite hash from URL
        if "t.me/joinchat/" in invite_url or "t.me/+" in invite_url:
            invite_hash = invite_url.split("/")[-1]
        else:
            invite_hash = invite_url
        
        try:
            from telethon.tl.functions.messages import ImportChatInviteRequest
            result = await client(ImportChatInviteRequest(invite_hash))
            logger.info(f"Successfully joined group via invite")
            # Get the entity after joining
            group_entity = await client.get_entity(result.chats[0])
            return group_entity
        except errors.InviteHashExpiredError:
            logger.warning("Invite link has expired or invalid")
            return None
        except errors.UsersTooMuchError:
            logger.error("Group is full")
            return None
        except errors.UserAlreadyParticipantError:
            logger.info("Already a member of the group (trying to find it in dialogs...)")
            # Try to get entity from invite link info
            try:
                from telethon.tl.functions.messages import CheckChatInviteRequest
                check_result = await client(CheckChatInviteRequest(invite_hash))
                if hasattr(check_result, 'chat'):
                    group_entity = check_result.chat
                    logger.info(f"Found group: {group_entity.title}")
                    return group_entity
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"Error joining group: {e}")
            return None
    except Exception as e:
        logger.error(f"Failed to join group: {e}")
        return None


async def find_or_join_group(client: TelegramClient) -> Optional[Channel]:
    """Find or join the target group using configured settings.
    
    Priority:
    1. Find by name (if GROUP_NAME is set)
    2. Try invite link (if GROUP_INVITE_URL is set)
    3. Use first group from dialogs
    
    Args:
        client: Telegram client instance
        
    Returns:
        Channel entity if found/joined, None otherwise
    """
    group_entity = None
    
    # Priority 1: Find by name
    if GROUP_NAME:
        logger.info(f"Searching for group by name: '{GROUP_NAME}'")
        group_entity = await find_group_by_name(client, GROUP_NAME)
    
    # Priority 2: Try invite link
    if not group_entity and GROUP_INVITE_URL:
        logger.info("Trying to join group via invite link...")
        group_entity = await join_group_via_invite(client, GROUP_INVITE_URL)
    
    # Priority 3: Use first group from dialogs
    if not group_entity:
        logger.warning("Group not found by name or invite. Trying to find first group from dialogs...")
        try:
            async for dialog in client.iter_dialogs(limit=50):
                if isinstance(dialog.entity, Channel) and not dialog.entity.broadcast:
                    group_entity = dialog.entity
                    logger.info(f"Using first group from dialogs: {group_entity.title}")
                    break
        except Exception as e:
            logger.error(f"Error finding group from dialogs: {e}")
    
    if not group_entity:
        logger.error("No group available!")
        logger.error("Options:")
        logger.error("  1. Set GROUP_NAME in .env (e.g., GROUP_NAME=My Group Name)")
        logger.error("  2. Set GROUP_INVITE_URL in .env with a valid invite link")
        logger.error("  3. Make sure you're a member of at least one group")
        return None
    
    logger.info(f"Target group found: {group_entity.title} (ID: {group_entity.id})")
    return group_entity

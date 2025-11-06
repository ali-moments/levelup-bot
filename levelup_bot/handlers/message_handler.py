"""Main message event handler and router."""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Message

from ..config.settings import MESSAGE_SENDER_USERNAME
from ..handlers.math_challenge import process_math_challenge
from ..handlers.box_handler import process_box_message
from pix2text import Pix2Text
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


async def handle_new_message(
    event: events.NewMessage.Event,
    client: TelegramClient,
    group_entity: Channel,
    ocr_model: Pix2Text | None,
    ocr_executor: ThreadPoolExecutor | None
):
    """Handle new messages from the bot.
    
    Args:
        event: NewMessage event
        client: Telegram client instance
        group_entity: Target group entity
        ocr_model: OCR model for math challenges
        ocr_executor: Thread pool executor for OCR
    """
    try:
        # Check if message is from the target group
        if not group_entity or event.chat_id != group_entity.id:
            logger.debug(f"Message not from target group. Chat ID: {event.chat_id}, Group ID: {group_entity.id if group_entity else None}")
            return
        
        # Get sender information
        sender = await event.get_sender()
        sender_username = None
        if sender:
            sender_username = getattr(sender, 'username', None)
            sender_id = getattr(sender, 'id', None)
            logger.debug(f"Message from sender: username={sender_username}, id={sender_id}")
        else:
            logger.debug("Message has no sender information")
        
        # Check if we should filter by sender username
        if MESSAGE_SENDER_USERNAME:
            # Only process messages from the specified username
            if not sender_username or sender_username != MESSAGE_SENDER_USERNAME:
                logger.debug(f"Message not from required sender. Expected: {MESSAGE_SENDER_USERNAME}, Got: {sender_username}")
                return
            logger.info(f"Message from required sender: {sender_username}")
        
        # Get message text (check both message text and caption for media messages)
        message_text = event.message.message or ""
        if not message_text and hasattr(event.message, 'raw_text'):
            message_text = event.message.raw_text or ""
        
        logger.debug(f"Message text: {message_text[:100] if message_text else '(empty)'}...")  # Log first 100 chars
        
        # Check for "چالش" (challenge) - can be in text or message might have photo
        has_challenge_keyword = "چالش" in message_text
        has_photo = bool(event.message.photo) or (hasattr(event.message, 'document') and event.message.document)
        
        # Process challenge if keyword is present, or if it's a photo (challenges are typically photos with math problems)
        if has_challenge_keyword:
            logger.info(f"Found challenge message (keyword detected) from {sender_username or 'unknown'}, processing...")
            # Process in background task to not block other operations
            asyncio.create_task(process_math_challenge(client, event.message, ocr_model, ocr_executor))
        elif has_photo:
            # Also process photos as they might be challenge images without the keyword in text
            logger.info(f"Found potential challenge message (photo detected) from {sender_username or 'unknown'}, processing...")
            # Process in background task to not block other operations
            asyncio.create_task(process_math_challenge(client, event.message, ocr_model, ocr_executor))
        
        # Check for "جعبه" (box)
        if "جعبه" in message_text:
            logger.info(f"Found box message from {sender_username or 'unknown'}, processing inline buttons...")
            # Process in background task to not block other operations
            asyncio.create_task(process_box_message(event.message))
            
    except Exception as e:
        logger.error(f"Error handling new message: {e}", exc_info=True)


"""Main message event handler and router."""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Message

from ..config.settings import MESSAGE_SENDER_USERNAME, ENABLE_MATH_CHALLENGES, ENABLE_BOX_MESSAGES
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
    print("\n" + "=" * 60)
    print("[DEBUG] MESSAGE HANDLER CALLED - EVENT RECEIVED!")
    print("=" * 60)
    
    try:
        # Verify client connection
        if not client:
            print("[DEBUG] ❌ ERROR: Client is None!")
            logger.error("Client is None in message handler")
            print("=" * 60)
            return
        
        is_connected = client.is_connected()
        print(f"[DEBUG] Client connected: {is_connected}")
        if not is_connected:
            print("[DEBUG] ⚠️  WARNING: Client is not connected!")
            logger.warning("Client is not connected when processing message")
            # Try to reconnect
            try:
                print("[DEBUG] Attempting to reconnect client...")
                if not client.is_connected():
                    await client.connect()
                    print("[DEBUG] ✅ Client reconnected")
                    logger.info("Client reconnected successfully")
            except Exception as reconnect_error:
                print(f"[DEBUG] ❌ Failed to reconnect: {reconnect_error}")
                logger.error(f"Failed to reconnect client: {reconnect_error}")
                print("=" * 60)
                return
        
        # Print event details
        print(f"[DEBUG] Event chat_id: {event.chat_id}")
        print(f"[DEBUG] Message ID: {event.message.id}")
        print(f"[DEBUG] Group entity: {group_entity.title if group_entity else None} (ID: {group_entity.id if group_entity else None})")
        
        # Normalize chat IDs for comparison (Telegram supergroups use negative IDs with -100 prefix)
        def normalize_chat_id(chat_id):
            """Normalize Telegram chat ID for comparison.
            
            Telegram supergroups have negative IDs like -1003174315970.
            The actual ID is embedded: abs(-1003174315970) - 1000000000000 = 3174315970
            """
            if chat_id is None:
                return None
            chat_id = int(chat_id)
            # If it's a supergroup ID (negative and large), extract the actual ID
            if chat_id < 0 and abs(chat_id) > 1000000000000:
                # Remove the -100 prefix: -1003174315970 -> 3174315970
                normalized = abs(chat_id) - 1000000000000
                return normalized
            return abs(chat_id)
        
        normalized_event_chat_id = normalize_chat_id(event.chat_id)
        normalized_group_id = normalize_chat_id(group_entity.id if group_entity else None)
        
        print(f"[DEBUG] Normalized event chat_id: {normalized_event_chat_id}")
        print(f"[DEBUG] Normalized group ID: {normalized_group_id}")
        
        # Check if message is from the target group
        if not group_entity or normalized_event_chat_id != normalized_group_id:
            print(f"[DEBUG] ❌ Message NOT from target group")
            print(f"[DEBUG]   Event chat_id (raw): {event.chat_id} (normalized: {normalized_event_chat_id})")
            print(f"[DEBUG]   Group ID (raw): {group_entity.id if group_entity else None} (normalized: {normalized_group_id})")
            logger.debug(f"Message not from target group. Chat ID: {event.chat_id} (normalized: {normalized_event_chat_id}), Group ID: {group_entity.id if group_entity else None} (normalized: {normalized_group_id})")
            print("=" * 60)
            return
        
        print(f"[DEBUG] ✅ Message IS from target group (IDs match after normalization)")
        logger.info(f"📨 New message received (Message ID: {event.message.id})")
        
        # Get sender information
        print("[DEBUG] Getting sender information...")
        sender = await event.get_sender()
        sender_username = None
        sender_id = None
        if sender:
            sender_username = getattr(sender, 'username', None)
            sender_id = getattr(sender, 'id', None)
            print(f"[DEBUG] Sender: @{sender_username or 'N/A'} (ID: {sender_id or 'N/A'})")
            logger.info(f"   👤 Sender: @{sender_username or 'N/A'} (ID: {sender_id or 'N/A'})")
        else:
            print("[DEBUG] ⚠️  Message has no sender information")
            logger.warning("   ⚠️  Message has no sender information")
        
        # Check if we should filter by sender username
        print(f"[DEBUG] MESSAGE_SENDER_USERNAME filter: {MESSAGE_SENDER_USERNAME or '(none - accept all)'}")
        if MESSAGE_SENDER_USERNAME:
            # Only process messages from the specified username
            if not sender_username or sender_username != MESSAGE_SENDER_USERNAME:
                print(f"[DEBUG] ❌ Skipping: Message not from required sender (@{MESSAGE_SENDER_USERNAME})")
                print(f"[DEBUG]   Actual sender: @{sender_username or 'N/A'}")
                logger.info(f"   ⏭️  Skipping: Message not from required sender (@{MESSAGE_SENDER_USERNAME})")
                print("=" * 60)
                return
            print(f"[DEBUG] ✅ Message from required sender: @{sender_username}")
            logger.info(f"   ✅ Message from required sender: @{sender_username}")
        else:
            print("[DEBUG] ✅ No sender filter - accepting message")
        
        # Get message text (check both message text and caption for media messages)
        print("[DEBUG] Extracting message text...")
        message_text = event.message.message or ""
        if not message_text and hasattr(event.message, 'raw_text'):
            message_text = event.message.raw_text or ""
        
        # Check for media
        has_photo = bool(event.message.photo) or (hasattr(event.message, 'document') and event.message.document)
        has_reply_markup = bool(event.message.reply_markup)
        
        print(f"[DEBUG] Message text: {message_text[:100] if message_text else '(empty)'}")
        print(f"[DEBUG] Has photo/document: {has_photo}")
        print(f"[DEBUG] Has inline buttons: {has_reply_markup}")
        logger.info(f"   📝 Message text: {message_text[:100] if message_text else '(empty)'}")
        logger.info(f"   🖼️  Has photo/document: {has_photo}")
        logger.info(f"   🔘 Has inline buttons: {has_reply_markup}")
        
        # Check for "چالش" (challenge) - can be in text or message might have photo
        print(f"[DEBUG] ENABLE_MATH_CHALLENGES: {ENABLE_MATH_CHALLENGES}")
        if ENABLE_MATH_CHALLENGES:
            has_challenge_keyword = "چالش" in message_text
            print(f"[DEBUG] Checking for math challenge...")
            print(f"[DEBUG]   Keyword 'چالش' found: {has_challenge_keyword}")
            print(f"[DEBUG]   Has photo: {has_photo}")
            
            # Process challenge if keyword is present, or if it's a photo (challenges are typically photos with math problems)
            if has_challenge_keyword:
                print("[DEBUG] ✅ Math Challenge DETECTED (keyword 'چالش' found)")
                logger.info(f"   ✅ Math Challenge DETECTED (keyword 'چالش' found)")
                logger.info(f"   🚀 Starting math challenge processing...")
                print("[DEBUG] 🚀 Creating task for math challenge processing...")
                # Process in background task to not block other operations
                asyncio.create_task(process_math_challenge(client, event.message, ocr_model, ocr_executor))
            elif has_photo:
                # Also process photos as they might be challenge images without the keyword in text
                print("[DEBUG] ✅ Potential Math Challenge DETECTED (photo/document found)")
                logger.info(f"   ✅ Potential Math Challenge DETECTED (photo/document found)")
                logger.info(f"   🚀 Starting math challenge processing...")
                print("[DEBUG] 🚀 Creating task for math challenge processing...")
                # Process in background task to not block other operations
                asyncio.create_task(process_math_challenge(client, event.message, ocr_model, ocr_executor))
            else:
                print("[DEBUG] ⏭️  Not a math challenge (no keyword 'چالش' and no photo)")
                logger.debug(f"   ⏭️  Not a math challenge (no keyword 'چالش' and no photo)")
        else:
            print("[DEBUG] ⏭️  Math challenges are disabled")
            logger.info(f"   ⏭️  Math challenges are disabled, skipping...")
        
        # Check for "جعبه" (box)
        print(f"[DEBUG] ENABLE_BOX_MESSAGES: {ENABLE_BOX_MESSAGES}")
        if ENABLE_BOX_MESSAGES:
            has_box_keyword = "جعبه" in message_text
            print(f"[DEBUG] Checking for box message...")
            print(f"[DEBUG]   Keyword 'جعبه' found: {has_box_keyword}")
            print(f"[DEBUG]   Has reply_markup: {has_reply_markup}")
            if has_box_keyword:
                print("[DEBUG] ✅ Box Message DETECTED (keyword 'جعبه' found)")
                logger.info(f"   ✅ Box Message DETECTED (keyword 'جعبه' found)")
                logger.info(f"   🚀 Starting box message processing...")
                print("[DEBUG] 🚀 Creating task for box message processing...")
                # Process in background task to not block other operations
                asyncio.create_task(process_box_message(client, event.message))
            else:
                print("[DEBUG] ⏭️  Not a box message (no keyword 'جعبه')")
                logger.debug(f"   ⏭️  Not a box message (no keyword 'جعبه')")
        else:
            print("[DEBUG] ⏭️  Box messages are disabled")
            logger.info(f"   ⏭️  Box messages are disabled, skipping...")
        
        print("[DEBUG] MESSAGE HANDLER COMPLETED")
        print("=" * 60 + "\n")
            
    except Exception as e:
        print(f"[DEBUG] ❌ ERROR in message handler: {e}")
        print("=" * 60)
        logger.error(f"Error handling new message: {e}", exc_info=True)
        import traceback
        print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")


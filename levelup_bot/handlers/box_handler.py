"""Box message processing handler."""

import logging
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors import PersistentTimestampOutdatedError

logger = logging.getLogger(__name__)


async def process_box_message(client: TelegramClient, message: Message):
    """Process box message: click all inline buttons.
    
    Args:
        client: Telegram client instance
        message: Message containing inline buttons
    """
    try:
        logger.info("=" * 60)
        logger.info("📦 BOX MESSAGE PROCESSING STARTED")
        logger.info(f"   Message ID: {message.id}")
        logger.info(f"   Chat ID: {getattr(message, 'chat_id', 'N/A')}")
        
        # Check if message has inline keyboard
        if not message.reply_markup:
            logger.warning("   ❌ Message does not have inline buttons (reply_markup is None)")
            logger.info("=" * 60)
            return
        
        logger.info("   ✅ Inline keyboard detected")
        
        # Get all buttons
        buttons_clicked = 0
        buttons_total = 0
        buttons_failed = 0
        buttons_skipped = 0
        
        if hasattr(message.reply_markup, 'rows'):
            total_rows = len(message.reply_markup.rows)
            logger.info(f"   📊 Found {total_rows} row(s) of buttons")
            row_index = 0
            for row in message.reply_markup.rows:
                buttons_in_row = len(row.buttons)
                logger.info(f"   📋 Row {row_index + 1}: {buttons_in_row} button(s)")
                button_index = 0
                for button in row.buttons:
                    buttons_total += 1
                    try:
                        # Try different methods to click the button
                        clicked = False
                        
                        # Method 1: Click by data attribute
                        if hasattr(button, 'data') and button.data:
                            try:
                                await message.click(data=button.data)
                                clicked = True
                                # Small delay between clicks to avoid rate limiting
                                await asyncio.sleep(0.5)
                            except PersistentTimestampOutdatedError:
                                logger.warning(f"⚠️  PersistentTimestampOutdatedError when clicking button, syncing session...")
                                try:
                                    await client.catch_up()
                                    logger.info("✅ Session synced, retrying button click...")
                                    await message.click(data=button.data)
                                    clicked = True
                                    await asyncio.sleep(0.5)
                                except Exception as retry_error:
                                    logger.debug(f"Failed to click button by data after sync: {retry_error}")
                                    pass
                            except Exception as e:
                                logger.debug(f"Failed to click button by data: {e}")
                                pass
                        
                        # Method 2: Click by index (if data method didn't work)
                        if not clicked:
                            try:
                                await message.click(row_index, button_index)
                                clicked = True
                                # Small delay between clicks to avoid rate limiting
                                await asyncio.sleep(0.5)
                            except PersistentTimestampOutdatedError:
                                logger.warning(f"⚠️  PersistentTimestampOutdatedError when clicking button, syncing session...")
                                try:
                                    await client.catch_up()
                                    logger.info("✅ Session synced, retrying button click...")
                                    await message.click(row_index, button_index)
                                    clicked = True
                                    await asyncio.sleep(0.5)
                                except Exception as retry_error:
                                    logger.debug(f"Failed to click button by index after sync: {retry_error}")
                                    pass
                            except Exception as e:
                                logger.debug(f"Failed to click button by index: {e}")
                                pass
                        
                        # Method 3: Try accessing nested button structure
                        if not clicked and hasattr(button, 'button') and hasattr(button.button, 'data') and button.button.data:
                            try:
                                await message.click(data=button.button.data)
                                clicked = True
                                # Small delay between clicks to avoid rate limiting
                                await asyncio.sleep(0.5)
                            except PersistentTimestampOutdatedError:
                                logger.warning(f"⚠️  PersistentTimestampOutdatedError when clicking button, syncing session...")
                                try:
                                    await client.catch_up()
                                    logger.info("✅ Session synced, retrying button click...")
                                    await message.click(data=button.button.data)
                                    clicked = True
                                    await asyncio.sleep(0.5)
                                except Exception as retry_error:
                                    logger.debug(f"Failed to click nested button after sync: {retry_error}")
                                    pass
                            except Exception as e:
                                logger.debug(f"Failed to click nested button: {e}")
                                pass
                        
                        # Method 4: Use client's request method directly
                        if not clicked and hasattr(button, 'data') and button.data:
                            try:
                                from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
                                # Get the peer from the message
                                peer = getattr(message, 'peer_id', None)
                                if not peer:
                                    # Try to get from chat_id
                                    peer = getattr(message, 'chat_id', None)
                                if not peer:
                                    # Try to get from input_chat
                                    peer = getattr(message, 'input_chat', None)
                                
                                if peer:
                                    result = await client(GetBotCallbackAnswerRequest(
                                        peer=peer,
                                        msg_id=message.id,
                                        data=button.data
                                    ))
                                    clicked = True
                                    await asyncio.sleep(0.5)
                            except PersistentTimestampOutdatedError:
                                logger.warning(f"⚠️  PersistentTimestampOutdatedError when clicking button, syncing session...")
                                try:
                                    await client.catch_up()
                                    logger.info("✅ Session synced, retrying button click...")
                                    if peer:
                                        result = await client(GetBotCallbackAnswerRequest(
                                            peer=peer,
                                            msg_id=message.id,
                                            data=button.data
                                        ))
                                        clicked = True
                                        await asyncio.sleep(0.5)
                                except Exception as retry_error:
                                    logger.debug(f"Failed to click button via client request after sync: {retry_error}")
                                    pass
                            except Exception as e:
                                logger.debug(f"Failed to click button via client request: {e}")
                                pass
                        
                        if clicked:
                            buttons_clicked += 1
                            button_info = ""
                            if hasattr(button, 'data') and button.data:
                                button_info = f"data: {button.data[:20] if len(button.data) > 20 else button.data}"
                            else:
                                button_info = f"index: [{row_index}, {button_index}]"
                            logger.info(f"   ✅ Button [{row_index}, {button_index}] clicked successfully - {button_info}")
                        elif hasattr(button, 'url'):
                            # URL button, can't click programmatically
                            buttons_skipped += 1
                            logger.info(f"   ⏭️  Button [{row_index}, {button_index}] is URL type, skipping")
                        else:
                            buttons_failed += 1
                            logger.warning(f"   ❌ Could not click button at [{row_index}, {button_index}]")
                        
                        button_index += 1
                    except Exception as e:
                        logger.error(f"Error clicking button at [{row_index}, {button_index}]: {e}")
                row_index += 1
        else:
            logger.warning("   ⚠️  Message has reply_markup but no 'rows' attribute")
        
        # Summary
        logger.info("")
        logger.info("   📊 PROCESSING SUMMARY:")
        logger.info(f"      Total buttons found: {buttons_total}")
        logger.info(f"      ✅ Successfully clicked: {buttons_clicked}")
        logger.info(f"      ❌ Failed to click: {buttons_failed}")
        logger.info(f"      ⏭️  Skipped (URL buttons): {buttons_skipped}")
        
        if buttons_clicked > 0:
            logger.info(f"   ✅ SUCCESS: Clicked {buttons_clicked} button(s)")
        elif buttons_total == 0:
            logger.warning("   ⚠️  No buttons found in message")
        else:
            logger.warning(f"   ❌ FAILED: Could not click any of {buttons_total} button(s)")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERROR processing box message: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())


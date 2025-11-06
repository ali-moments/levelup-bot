"""Box message processing handler."""

import logging
from telethon.tl.types import Message

logger = logging.getLogger(__name__)


async def process_box_message(message: Message):
    """Process box message: click all inline buttons.
    
    Args:
        message: Message containing inline buttons
    """
    try:
        # Check if message has inline keyboard
        if not message.reply_markup:
            logger.info("Message does not have inline buttons")
            return
        
        # Get all buttons
        buttons_clicked = 0
        if hasattr(message.reply_markup, 'rows'):
            row_index = 0
            for row in message.reply_markup.rows:
                button_index = 0
                for button in row.buttons:
                    try:
                        # Try different methods to click the button
                        clicked = False
                        
                        # Method 1: Click by data attribute
                        if hasattr(button, 'data') and button.data:
                            try:
                                await message.click(data=button.data)
                                clicked = True
                            except:
                                pass
                        
                        # Method 2: Click by index (if data method didn't work)
                        if not clicked:
                            try:
                                await message.click(row_index, button_index)
                                clicked = True
                            except:
                                pass
                        
                        # Method 3: Try accessing nested button structure
                        if not clicked and hasattr(button, 'button') and hasattr(button.button, 'data') and button.button.data:
                            try:
                                await message.click(data=button.button.data)
                                clicked = True
                            except:
                                pass
                        
                        if clicked:
                            buttons_clicked += 1
                            button_info = ""
                            if hasattr(button, 'data') and button.data:
                                button_info = f"data: {button.data[:20] if len(button.data) > 20 else button.data}"
                            else:
                                button_info = f"index: [{row_index}, {button_index}]"
                            logger.info(f"Clicked button with {button_info}")
                        elif hasattr(button, 'url'):
                            # URL button, can't click programmatically
                            logger.info("Button is URL type, skipping")
                        else:
                            logger.warning(f"Could not click button at [{row_index}, {button_index}]")
                        
                        button_index += 1
                    except Exception as e:
                        logger.error(f"Error clicking button at [{row_index}, {button_index}]: {e}")
                row_index += 1
        
        logger.info(f"Clicked {buttons_clicked} inline buttons")
        
    except Exception as e:
        logger.error(f"Error processing box message: {e}")


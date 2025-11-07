"""Math challenge processing handler."""

import asyncio
import os
import tempfile
import logging
from typing import Optional
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors import PersistentTimestampOutdatedError
from pix2text import Pix2Text
from concurrent.futures import ThreadPoolExecutor

from ..ocr.math_solver import parse_and_solve_math

logger = logging.getLogger(__name__)


async def process_math_challenge(
    client: TelegramClient,
    message: Message,
    ocr_model: Optional[Pix2Text],
    ocr_executor: Optional[ThreadPoolExecutor]
):
    """Process math challenge message: download image, OCR, solve, and reply.
    
    Args:
        client: Telegram client instance
        message: Message containing the challenge image
        ocr_model: Initialized OCR model
        ocr_executor: Thread pool executor for OCR operations
    """
    try:
        logger.info("=" * 60)
        logger.info("🔢 MATH CHALLENGE PROCESSING STARTED")
        logger.info(f"   Message ID: {message.id}")
        logger.info(f"   Chat ID: {getattr(message, 'chat_id', 'N/A')}")
        
        # Check if message has photo
        has_photo = bool(message.photo)
        has_document = bool(message.document)
        
        logger.info(f"   🖼️  Has photo: {has_photo}")
        logger.info(f"   📄 Has document: {has_document}")
        
        if not has_photo and not has_document:
            logger.warning("   ❌ Message does not contain image (no photo or document)")
            logger.info("=" * 60)
            return
        
        # Download the image (async, won't block)
        logger.info("   ⬇️  Downloading image from message...")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.close()
        
        try:
            try:
                await client.download_media(message, temp_file.name)
            except PersistentTimestampOutdatedError:
                logger.warning("   ⚠️  PersistentTimestampOutdatedError when downloading, syncing session...")
                await client.catch_up()
                logger.info("   ✅ Session synced, retrying download...")
                await client.download_media(message, temp_file.name)
            
            file_size = os.path.getsize(temp_file.name) if os.path.exists(temp_file.name) else 0
            logger.info(f"   ✅ Image downloaded successfully")
            logger.info(f"      File: {temp_file.name}")
            logger.info(f"      Size: {file_size / 1024:.2f} KB")
            
            # Use OCR to extract text
            if not ocr_model or not ocr_executor:
                logger.error("   ❌ OCR model or executor not initialized")
                logger.info("=" * 60)
                return
            
            logger.info("   🔍 Extracting text from image using OCR...")
            logger.info("      (This may take a few seconds)")
            
            # Run blocking OCR operation in thread pool to avoid blocking event loop
            # This allows word sending and other operations to continue
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                ocr_executor,
                ocr_model.recognize,
                temp_file.name
            )
            
            logger.info("   ✅ OCR processing completed")
            
            # Extract text from result
            # pix2text returns a string or a structured result
            extracted_text = ""
            if isinstance(result, str):
                extracted_text = result
            elif isinstance(result, dict):
                # If result is a dict, try common keys
                extracted_text = result.get('text', result.get('out_text', result.get('formula', result.get('latex', ''))))
            elif isinstance(result, list):
                # If result is a list, try to extract text from each item
                text_parts = []
                for item in result:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        text_parts.append(item.get('text', item.get('out_text', item.get('formula', item.get('latex', '')))))
                    elif hasattr(item, 'text'):
                        text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                extracted_text = ' '.join(text_parts)
            elif hasattr(result, 'text'):
                extracted_text = result.text
            elif hasattr(result, 'out_text'):
                extracted_text = result.out_text
            elif hasattr(result, 'formula'):
                extracted_text = result.formula
            elif hasattr(result, 'latex'):
                extracted_text = result.latex
            else:
                # Try to convert to string
                extracted_text = str(result)
            
            # Clean up extracted text
            extracted_text = extracted_text.strip()
            logger.info(f"   📝 Extracted text: '{extracted_text}'")
            
            if not extracted_text:
                logger.warning("   ❌ No text extracted from image")
                logger.info("=" * 60)
                return
            
            # Parse and solve math problem (fast, synchronous is fine)
            logger.info("   🧮 Parsing and solving math expression...")
            answer = parse_and_solve_math(extracted_text)
            
            if answer is not None:
                # Reply with the answer (async, won't block)
                reply_text = str(int(answer) if answer.is_integer() else answer)
                logger.info(f"   ✅ Solution found: {extracted_text} = {reply_text}")
                logger.info(f"   📤 Sending reply...")
                try:
                    await message.reply(reply_text)
                except PersistentTimestampOutdatedError:
                    logger.warning("   ⚠️  PersistentTimestampOutdatedError when replying, syncing session...")
                    await client.catch_up()
                    logger.info("   ✅ Session synced, retrying reply...")
                    await message.reply(reply_text)
                logger.info(f"   ✅ Successfully replied with answer: {reply_text}")
                logger.info("=" * 60)
            else:
                logger.warning(f"   ❌ Could not parse or solve math problem")
                logger.warning(f"      Extracted text: '{extracted_text}'")
                logger.info("=" * 60)
                
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    logger.debug(f"   🗑️  Temporary file deleted: {temp_file.name}")
            except Exception as cleanup_error:
                logger.warning(f"   ⚠️  Failed to delete temp file: {cleanup_error}")
                
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERROR processing math challenge: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())


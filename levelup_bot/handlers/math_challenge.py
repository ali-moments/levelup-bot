"""Math challenge processing handler."""

import asyncio
import os
import tempfile
import logging
from typing import Optional
from telethon import TelegramClient
from telethon.tl.types import Message
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
        # Check if message has photo
        if not message.photo and not message.document:
            logger.warning("Message does not contain image")
            return
        
        # Download the image (async, won't block)
        logger.info("Downloading image from message...")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.close()
        
        try:
            await client.download_media(message, temp_file.name)
            logger.info(f"Image downloaded to {temp_file.name}")
            
            # Use OCR to extract text
            if not ocr_model or not ocr_executor:
                logger.error("OCR model or executor not initialized")
                return
            
            logger.info("Extracting text from image using OCR (async)...")
            # Run blocking OCR operation in thread pool to avoid blocking event loop
            # This allows word sending and other operations to continue
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                ocr_executor,
                ocr_model.recognize,
                temp_file.name
            )
            
            # Extract text from result
            # pix2text returns a string or a structured result
            extracted_text = ""
            if isinstance(result, str):
                extracted_text = result
            elif isinstance(result, dict):
                # If result is a dict, try common keys
                extracted_text = result.get('text', result.get('out_text', result.get('formula', '')))
            elif hasattr(result, 'text'):
                extracted_text = result.text
            elif hasattr(result, 'out_text'):
                extracted_text = result.out_text
            elif hasattr(result, 'formula'):
                extracted_text = result.formula
            else:
                # Try to convert to string
                extracted_text = str(result)
            
            logger.info(f"Extracted text: {extracted_text}")
            
            # Parse and solve math problem (fast, synchronous is fine)
            answer = parse_and_solve_math(extracted_text)
            
            if answer is not None:
                # Reply with the answer (async, won't block)
                reply_text = str(int(answer) if answer.is_integer() else answer)
                await message.reply(reply_text)
                logger.info(f"Replied with answer: {reply_text}")
            else:
                logger.warning("Could not parse or solve math problem from extracted text")
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error processing math challenge: {e}")


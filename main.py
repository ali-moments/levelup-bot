import asyncio
import logging
import queue
import random
import re
import signal
import sys
import threading
import time
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Set environment variables early to force CPU usage for ONNX Runtime
# This must be done before importing pix2text or any ONNX-dependent libraries
os.environ['ONNXRUNTIME_EXECUTION_PROVIDER'] = 'CPUExecutionProvider'
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide CUDA devices to force CPU

# Patch ONNX Runtime BEFORE importing pix2text to force CPU usage
try:
    import onnxruntime as ort
    
    # Store original functions
    _original_get_available_providers = ort.get_available_providers
    _original_InferenceSession = ort.InferenceSession
    
    def _get_available_providers_cpu_only():
        """Return only CPU-compatible providers."""
        providers = _original_get_available_providers()
        # Filter to only CPU and Azure providers (both work on CPU)
        cpu_providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
        # Always include CPUExecutionProvider as first choice
        if 'CPUExecutionProvider' not in cpu_providers:
            cpu_providers.insert(0, 'CPUExecutionProvider')
        return cpu_providers
    
    def _InferenceSession_cpu_only(model_path, sess_options=None, providers=None, provider_options=None, **kwargs):
        """Create InferenceSession with CPU providers only."""
        # Force CPU providers
        if providers is None:
            providers = _get_available_providers_cpu_only()
        else:
            # Filter providers to only CPU-compatible ones
            providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
            if not providers:
                providers = ['CPUExecutionProvider']
        
        # Remove CUDA from providers if somehow it got in
        providers = [p for p in providers if 'CUDA' not in p]
        
        try:
            return _original_InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=providers,
                provider_options=provider_options,
                **kwargs
            )
        except ValueError as e:
            # If still fails, try with only CPUExecutionProvider
            if 'CUDAExecutionProvider' in str(e):
                providers = ['CPUExecutionProvider']
                return _original_InferenceSession(
                    model_path,
                    sess_options=sess_options,
                    providers=providers,
                    provider_options=provider_options,
                    **kwargs
                )
            raise
    
    # Apply patches immediately
    ort.get_available_providers = _get_available_providers_cpu_only
    ort.InferenceSession = _InferenceSession_cpu_only
except ImportError:
    # onnxruntime not available yet, will patch later
    pass

from telethon import TelegramClient, errors, events
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel
from pix2text import Pix2Text

from constants import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    GROUP_INVITE_URL,
    GROUP_NAME,
    BONUS_MESSAGE,
    BONUS_INTERVAL,
    ENABLE_WORD_SENDING,
    WORD_SENDER_SLOW_MODE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose warnings from RapidOCR and other libraries
logging.getLogger('RapidOCR').setLevel(logging.ERROR)
logging.getLogger('cnstd').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.ERROR)  # Suppress use_fast warnings
logging.getLogger('optimum').setLevel(logging.ERROR)  # Suppress ONNX warnings
logging.getLogger('optimum.onnxruntime').setLevel(logging.ERROR)

# Global variables
client: Optional[TelegramClient] = None
event_loop: Optional[asyncio.AbstractEventLoop] = None
wordlist: list[str] = []
message_queue: queue.Queue = queue.Queue()
running = True
group_entity = None
shutdown_event: Optional[asyncio.Event] = None  # Global shutdown event
worker_thread: Optional[threading.Thread] = None  # Worker thread reference

# Message rate based on WORD_SENDER setting
# If WORD_SENDER is True: 900-1100 messages/hour (3.27-4.0s delay)
# If WORD_SENDER is False: 100-150 messages/hour (24-36s delay)
if WORD_SENDER_SLOW_MODE:
    # 900 msg/h = 4.0s delay, 1100 msg/h = 3.27s delay
    MIN_MESSAGE_DELAY = 3.27  # 1100 messages/hour
    MAX_MESSAGE_DELAY = 4.0   # 900 messages/hour
else:
    # 100 msg/h = 36s delay, 150 msg/h = 24s delay
    MIN_MESSAGE_DELAY = 24.0  # 150 messages/hour
    MAX_MESSAGE_DELAY = 36.0  # 100 messages/hour

ocr_model: Optional[Pix2Text] = None
ocr_executor: Optional[ThreadPoolExecutor] = None  # Thread pool for blocking OCR operations


def load_wordlist(filename: str = "wordlist.txt") -> list[str]:
    """Load words from wordlist.txt file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(words)} words from {filename}")
        return words
    except FileNotFoundError:
        logger.error(f"Wordlist file '{filename}' not found!")
        return []
    except Exception as e:
        logger.error(f"Error loading wordlist: {e}")
        return []


async def initialize_client():
    """Initialize and connect Telegram client."""
    global client, event_loop
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        event_loop = client.loop
        logger.info("Telegram client connected successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        return False


async def find_group_by_name(group_name: str):
    """Find a group by name from dialogs."""
    global group_entity
    try:
        if not group_name:
            return False
        
        logger.info(f"Searching for group: '{group_name}' in dialogs...")
        async for dialog in client.iter_dialogs():
            if isinstance(dialog.entity, Channel) and not dialog.entity.broadcast:
                # Check if the title matches (case-insensitive)
                if dialog.entity.title.lower() == group_name.lower():
                    group_entity = dialog.entity
                    logger.info(f"Found group: {group_entity.title}")
                    return True
        
        logger.warning(f"Group '{group_name}' not found in dialogs")
        return False
    except Exception as e:
        logger.error(f"Error finding group by name: {e}")
        return False


async def join_group_via_invite(invite_url: str):
    """Join a group using an invite link."""
    global group_entity
    try:
        if not invite_url:
            return False
        
        # Extract invite hash from URL
        if "t.me/joinchat/" in invite_url or "t.me/+" in invite_url:
            invite_hash = invite_url.split("/")[-1]
        else:
            invite_hash = invite_url
        
        try:
            result = await client(ImportChatInviteRequest(invite_hash))
            logger.info(f"Successfully joined group via invite")
            # Get the entity after joining
            group_entity = await client.get_entity(result.chats[0])
            return True
        except errors.InviteHashExpiredError:
            logger.warning("Invite link has expired or invalid")
            return False
        except errors.UsersTooMuchError:
            logger.error("Group is full")
            return False
        except errors.UserAlreadyParticipantError:
            logger.info("Already a member of the group (trying to find it in dialogs...)")
            # Try to get entity from invite link info
            try:
                from telethon.tl.functions.messages import CheckChatInviteRequest
                check_result = await client(CheckChatInviteRequest(invite_hash))
                if hasattr(check_result, 'chat'):
                    group_entity = check_result.chat
                    logger.info(f"Found group: {group_entity.title}")
                    return True
            except:
                pass
            return False
        except Exception as e:
            logger.error(f"Error joining group: {e}")
            return False
    except Exception as e:
        logger.error(f"Failed to join group: {e}")
        return False


async def send_message_to_group(message: str):
    """Send a message to the group."""
    global group_entity
    try:
        if not group_entity:
            logger.error("Group entity not set")
            return False
        
        await client.send_message(group_entity, message)
        logger.info(f"Sent message to group: {message[:50]}...")
        return True
    except errors.FloodWaitError as e:
        logger.warning(f"Rate limited. Waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        logger.error(f"Error sending message to group: {e}")
        return False


async def send_bonus_message():
    """Send bonus message to the group."""
    global group_entity
    try:
        if not group_entity:
            logger.error("Group entity not set")
            return False
        
        await client.send_message(group_entity, BONUS_MESSAGE)
        logger.info(f"Sent bonus message to group: {BONUS_MESSAGE}")
        return True
    except errors.FloodWaitError as e:
        logger.warning(f"Rate limited. Waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        logger.error(f"Error sending bonus message: {e}")
        return False


def message_worker():
    """Worker thread that processes messages from the queue."""
    global running, event_loop
    
    while running:
        try:
            # Wait for event loop to be available
            if not event_loop:
                time.sleep(0.5)
                continue
            
            # Get message from queue (with timeout to check running flag)
            try:
                message_data = message_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            if message_data is None:  # Shutdown signal
                break
            
            message_type = message_data.get('type')
            
            if message_type == 'word':
                # Send word message
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        send_message_to_group(message_data['message']),
                        event_loop
                    )
                    future.result(timeout=10)  # Wait up to 10 seconds
                except Exception as e:
                    logger.error(f"Error sending word message: {e}")
                
                # Random delay between MIN and MAX to achieve 900-1100 messages/hour
                # Check running flag during sleep to exit quickly
                delay = random.uniform(MIN_MESSAGE_DELAY, MAX_MESSAGE_DELAY)
                elapsed = 0
                while elapsed < delay and running:
                    sleep_chunk = min(0.5, delay - elapsed)  # Check every 0.5 seconds
                    time.sleep(sleep_chunk)
                    elapsed += sleep_chunk
                
            message_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error in message worker: {e}")
            time.sleep(5)


async def bonus_message_loop():
    """Async loop that sends bonus messages every 181 seconds (3 minutes + 1 second) with precise timing."""
    global running
    import time as time_module
    
    # Send first bonus message immediately
    if running:
        logger.info("Sending first bonus message immediately...")
        await send_bonus_message()
        last_send_time = time_module.time()  # Track when message was actually sent
        logger.info(f"First bonus message sent. Next in {BONUS_INTERVAL} seconds...")
    
    # Then send every 181 seconds with precise timing
    while running:
        try:
            # Calculate sleep time based on when message was actually sent
            current_time = time_module.time()
            time_since_last_send = current_time - last_send_time
            sleep_time = BONUS_INTERVAL - time_since_last_send
            
            # If we're already past the interval, send immediately
            if sleep_time <= 0:
                sleep_time = 0
            else:
                await asyncio.sleep(sleep_time)
            
            if running:
                logger.info(f"Sending bonus message (every {BONUS_INTERVAL}s = 3 minutes + 1 second)...")
                await send_bonus_message()
                last_send_time = time_module.time()  # Update last send time to actual send completion
                logger.info(f"Bonus message sent. Next in {BONUS_INTERVAL} seconds...")
        except asyncio.CancelledError:
            logger.info("Bonus message loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in bonus message loop: {e}")
            if running:
                await asyncio.sleep(5)


async def initialize_ocr_model():
    """Initialize the OCR model for math problem recognition - CPU only."""
    global ocr_model, ocr_executor
    import warnings
    import onnxruntime as ort
    
    # Suppress ALL warnings
    warnings.filterwarnings('ignore')
    
    # Force CPU mode - ensure environment variables are set
    os.environ['ONNXRUNTIME_EXECUTION_PROVIDER'] = 'CPUExecutionProvider'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide CUDA devices
    
    # Ensure CPU patches are applied (use module-level patches if available)
    try:
        # Check if module-level patches exist
        if '_get_available_providers_cpu_only' in globals() and '_InferenceSession_cpu_only' in globals():
            # Use module-level patches
            if not hasattr(ort, '_original_get_available_providers'):
                ort._original_get_available_providers = ort.get_available_providers
                ort._original_InferenceSession = ort.InferenceSession
            ort.get_available_providers = _get_available_providers_cpu_only
            ort.InferenceSession = _InferenceSession_cpu_only
        else:
            # Apply patches inline if module-level ones don't exist
            if not hasattr(ort, '_original_get_available_providers'):
                ort._original_get_available_providers = ort.get_available_providers
                ort._original_InferenceSession = ort.InferenceSession
            
            def get_cpu_providers():
                """Return only CPU providers."""
                providers = ort._original_get_available_providers()
                cpu_providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
                if not cpu_providers:
                    cpu_providers = ['CPUExecutionProvider']
                return cpu_providers
            
            def create_cpu_session(model_path, sess_options=None, providers=None, provider_options=None, **kwargs):
                """Create InferenceSession with CPU providers only."""
                if providers is None:
                    providers = get_cpu_providers()
                else:
                    # Filter to only CPU-compatible providers
                    providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
                    if not providers:
                        providers = ['CPUExecutionProvider']
                
                # Remove any CUDA providers
                providers = [p for p in providers if 'CUDA' not in p]
                
                try:
                    return ort._original_InferenceSession(
                        model_path,
                        sess_options=sess_options,
                        providers=providers,
                        provider_options=provider_options,
                        **kwargs
                    )
                except ValueError as e:
                    # If still fails, try with only CPUExecutionProvider
                    if 'CUDA' in str(e) or 'cuda' in str(e):
                        providers = ['CPUExecutionProvider']
                        return ort._original_InferenceSession(
                            model_path,
                            sess_options=sess_options,
                            providers=providers,
                            provider_options=provider_options,
                            **kwargs
                        )
                    raise
            
            ort.get_available_providers = get_cpu_providers
            ort.InferenceSession = create_cpu_session
    except Exception as e:
        logger.debug(f"Error applying CPU patches: {e}")
    
    # Initialize OCR model with CPU only
    logger.info("Initializing OCR model with CPU only...")
    
    # Try different initialization methods
    initialization_methods = [
        # Method 1: Try with formula recognition model
        lambda: Pix2Text.from_config(dict(
            formula=dict(model_name='breezedeus/pix2text-mfr')
        )),
        # Method 2: Simple initialization
        lambda: Pix2Text(),
    ]
    
    for i, init_method in enumerate(initialization_methods, 1):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                logger.info(f"Trying OCR initialization method {i}...")
                ocr_model = init_method()
                ocr_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr")
                logger.info("OCR model initialized successfully - Running on CPU")
                return True
        except Exception as e:
            logger.warning(f"OCR initialization method {i} failed: {e}")
            if i == len(initialization_methods):
                # Last method failed, log the error
                logger.error(f"All OCR initialization methods failed. Last error: {e}")
                logger.warning("OCR initialization failed. Math challenge processing disabled.")
                return False
            continue
    
    # Should not reach here, but just in case
    logger.warning("OCR initialization failed. Math challenge processing disabled.")
    return False


def parse_and_solve_math(text: str) -> Optional[float]:
    """Parse math expression from text and solve it."""
    try:
        # Clean the text and extract math expression
        # Handle patterns like "12 + 3 = ?" or "12+3=?"
        # Replace Persian operators with standard ones
        text = text.replace('×', '*').replace('÷', '/').replace('=', '').replace('?', '').strip()
        
        # Try to find math expression pattern
        # Match patterns like: number operator number
        pattern = r'(\d+)\s*([+\-*/])\s*(\d+)'
        match = re.search(pattern, text)
        
        if match:
            num1 = float(match.group(1))
            operator = match.group(2)
            num2 = float(match.group(3))
            
            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                if num2 == 0:
                    return None
                result = num1 / num2
            else:
                return None
            
            return result
        
        # If no pattern match, try to evaluate the entire expression safely
        # Remove any non-math characters
        cleaned = re.sub(r'[^\d+\-*/.() ]', '', text)
        if cleaned:
            try:
                result = eval(cleaned)
                return float(result) if isinstance(result, (int, float)) else None
            except:
                pass
        
        return None
    except Exception as e:
        logger.error(f"Error parsing math expression: {e}")
        return None


async def process_math_challenge(message):
    """Process math challenge message: download image, OCR, solve, and reply."""
    global ocr_model, ocr_executor
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


async def process_box_message(message):
    """Process box message: click all inline buttons."""
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


async def handle_new_message(event):
    """Handle new messages from the bot."""
    global group_entity
    
    try:
        # Check if message is from the target group
        if not group_entity or event.chat_id != group_entity.id:
            return
        
        # Check if message is from @seyed_ali_khamenei_bot
        sender = await event.get_sender()
        if not sender or (hasattr(sender, 'username') and sender.username != 'seyed_ali_khamenei_bot'):
            return
        
        message_text = event.message.message or ""
        
        # Check for "چالش" (challenge)
        if "چالش" in message_text:
            logger.info("Found challenge message, processing...")
            # Process in background task to not block other operations
            asyncio.create_task(process_math_challenge(event.message))
        
        # Check for "جعبه" (box)
        elif "جعبه" in message_text:
            logger.info("Found box message, processing inline buttons...")
            # Process in background task to not block other operations
            asyncio.create_task(process_box_message(event.message))
            
    except Exception as e:
        logger.error(f"Error handling new message: {e}")


async def main_loop():
    """Main loop that sends random words to the group."""
    global running
    
    if not ENABLE_WORD_SENDING:
        logger.info("Word sending is disabled. Exiting main loop.")
        return
    
    if not wordlist:
        logger.error("Wordlist is empty. Cannot send messages.")
        return
    
    # Calculate messages per hour for logging
    if WORD_SENDER_SLOW_MODE:
        rate_info = "900-1100 messages/hour"
    else:
        rate_info = "100-150 messages/hour"
    
    logger.info(f"Starting main message loop ({MIN_MESSAGE_DELAY}-{MAX_MESSAGE_DELAY}s delay = {rate_info})...")
    
    while running:
        try:
            # Select random word
            word = random.choice(wordlist)
            
            # Add message to queue
            message_queue.put({
                'type': 'word',
                'message': word
            })
            
            logger.info(f"Queued word: {word}")
            
            # Random delay between MIN and MAX
            delay = random.uniform(MIN_MESSAGE_DELAY, MAX_MESSAGE_DELAY)
            await asyncio.sleep(delay)
            
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)


async def main():
    """Main async function."""
    global running, wordlist, client, group_entity, shutdown_event, worker_thread
    
    # Load wordlist (only if word sending is enabled)
    if ENABLE_WORD_SENDING:
        wordlist = load_wordlist()
        if not wordlist:
            logger.error("Cannot proceed without wordlist when word sending is enabled")
            return
    else:
        logger.info("Word sending is disabled. Skipping wordlist loading.")
        wordlist = []
    
    # Initialize client
    if not await initialize_client():
        logger.error("Failed to initialize client")
        return
    
    # Find or join group
    # Priority: 1) Find by name, 2) Try invite link, 3) Use first group from dialogs
    
    if GROUP_NAME:
        await find_group_by_name(GROUP_NAME)
    
    if not group_entity and GROUP_INVITE_URL:
        await join_group_via_invite(GROUP_INVITE_URL)
    
    # If still not found, try to get first group from dialogs
    if not group_entity:
        logger.warning("No group entity found. Trying to find first group from dialogs...")
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
        return
    
    # Initialize OCR model
    logger.info("Initializing OCR model...")
    if not await initialize_ocr_model():
        logger.warning("Failed to initialize OCR model, math challenge processing may not work")
    
    # Register message event handler
    client.add_event_handler(handle_new_message, events.NewMessage(chats=group_entity))
    logger.info("Message event handler registered")
    
    # Start worker thread
    worker_thread = threading.Thread(target=message_worker, daemon=True)
    worker_thread.start()
    logger.info("Message worker thread started")
    
    # Start bonus message loop as async task (independent, not affected by word message delays)
    bonus_loop_task = asyncio.create_task(bonus_message_loop())
    logger.info(f"Bonus message loop started (interval: {BONUS_INTERVAL}s, target: group)")
    
    # Start main loop in background (only if word sending is enabled)
    if ENABLE_WORD_SENDING:
        main_loop_task = asyncio.create_task(main_loop())
        logger.info("Word sending loop started")
    else:
        logger.info("Word sending is disabled. Main loop will not start.")
        main_loop_task = None
    
    # Create a shutdown event (make it global so signal handler can access it)
    shutdown_event = asyncio.Event()
    
    try:
        # Keep running until interrupted
        await shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except asyncio.CancelledError:
        logger.info("Tasks cancelled, shutting down...")
    finally:
        running = False
        shutdown_event.set()  # Signal shutdown
        
        # Cancel all running tasks
        logger.info("Cancelling running tasks...")
        tasks_to_cancel = [bonus_loop_task]
        if main_loop_task:
            tasks_to_cancel.append(main_loop_task)
        for task in tasks_to_cancel:
            task.cancel()
        
        # Wait for tasks to finish cancelling (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            logger.warning("Tasks did not cancel within timeout")
        except Exception as e:
            logger.debug(f"Error during task cancellation: {e}")
        
        # Signal worker thread to stop
        message_queue.put(None)  # Shutdown signal
        
        # Wait for worker thread to finish (with timeout)
        if worker_thread and worker_thread.is_alive():
            logger.info("Waiting for worker thread to finish...")
            worker_thread.join(timeout=2.0)
            if worker_thread.is_alive():
                logger.warning("Worker thread did not stop within timeout")
        
        # Don't wait for queue to empty - just clear it
        # The worker thread should have processed the shutdown signal
        
        # Shutdown OCR executor
        global ocr_executor
        if ocr_executor:
            logger.info("Shutting down OCR executor...")
            ocr_executor.shutdown(wait=False)  # Don't wait, just shutdown
        
        if client:
            logger.info("Disconnecting Telegram client...")
            try:
                await asyncio.wait_for(client.disconnect(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Client disconnect timed out")
            except Exception as e:
                logger.debug(f"Error disconnecting client: {e}")
        
        logger.info("Bot stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global running, event_loop, shutdown_event
    logger.info(f"Received shutdown signal ({signum})")
    running = False
    
    # Use the global event_loop if available
    current_loop = event_loop
    
    # If event loop is running, set the shutdown event to break out of wait
    if current_loop and current_loop.is_running() and shutdown_event:
        # Schedule setting the shutdown event in the event loop (thread-safe)
        def set_shutdown():
            shutdown_event.set()
        current_loop.call_soon_threadsafe(set_shutdown)
        
        # Also cancel all tasks to ensure quick shutdown
        try:
            tasks = [task for task in asyncio.all_tasks(current_loop) if not task.done()]
            for task in tasks:
                task.cancel()
        except Exception as e:
            logger.debug(f"Error cancelling tasks: {e}")
    elif shutdown_event:
        # If shutdown_event exists but loop isn't running or available,
        # try to set it directly (this is safe if called before event loop starts)
        try:
            shutdown_event.set()
        except:
            pass


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        running = False
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        running = False
    
    # Force exit to ensure process terminates
    # This ensures the process exits even if there are hanging threads
    logger.info("Exiting process...")
    sys.exit(0)


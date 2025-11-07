"""Main bot orchestrator class."""

import asyncio
import logging
import queue
import threading
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from telethon import TelegramClient, events
from telethon.tl.types import Channel
from pix2text import Pix2Text

from .config.settings import (
    ENABLE_WORD_SENDING,
    BONUS_INTERVAL_MIN,
    BONUS_INTERVAL_MAX,
    MESSAGE_SENDER_USERNAME,
    ENABLE_MATH_CHALLENGES,
    ENABLE_BOX_MESSAGES,
    ENABLE_BONUS_MESSAGES,
    AUTO_DELETE_WORD_MESSAGES,
)
from .config.logging_config import setup_logging
from .telegram.client import initialize_client
from .telegram.group import find_or_join_group
from .telegram.messaging import send_message_to_group
from .handlers.message_handler import handle_new_message
from .services.message_worker import message_worker
from .services.word_sender import word_sender_loop
from .services.bonus_sender import bonus_message_loop
from .ocr.model import initialize_ocr_model
from .ocr.cpu_patch import apply_cpu_patches
from .utils.wordlist import load_wordlist
from .utils.shutdown import setup_signal_handlers

logger = logging.getLogger(__name__)


class Bot:
    """Main bot orchestrator that coordinates all components."""
    
    def __init__(self):
        """Initialize the bot."""
        # Apply CPU patches early
        apply_cpu_patches()
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.client: Optional[TelegramClient] = None
        self.group_entity: Optional[Channel] = None
        self.ocr_model: Optional[Pix2Text] = None
        self.ocr_executor: Optional[ThreadPoolExecutor] = None
        
        # State management
        self.running = asyncio.Event()
        self.running.set()  # Start as running
        self.shutdown_event: Optional[asyncio.Event] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Services
        self.wordlist: list[str] = []
        self.message_queue: queue.Queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.worker_running = threading.Event()
        self.worker_running.set()
        
        # Tasks
        self.bonus_loop_task: Optional[asyncio.Task] = None
        self.word_sender_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize all bot components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        # Print startup banner
        self.logger.info("=" * 60)
        self.logger.info("🚀 LevelUp Bot - Starting...")
        self.logger.info("=" * 60)
        
        # Print configuration summary
        self._print_config_summary()
        
        # Load wordlist (only if word sending is enabled)
        self.logger.info("📂 Loading wordlist...")
        if ENABLE_WORD_SENDING:
            self.wordlist = load_wordlist()
            if not self.wordlist:
                self.logger.error("❌ Cannot proceed without wordlist when word sending is enabled")
                return False
            self.logger.info(f"✅ Wordlist loaded: {len(self.wordlist)} words")
        else:
            self.logger.info("⏭️  Word sending is disabled. Skipping wordlist loading.")
            self.wordlist = []
        
        # Initialize client
        self.logger.info("🔌 Connecting to Telegram...")
        self.client = await initialize_client()
        if not self.client:
            self.logger.error("❌ Failed to initialize client")
            return False
        self.logger.info("✅ Telegram client connected successfully")
        self.event_loop = self.client.loop
        
        # Find or join group
        self.logger.info("🔍 Finding target group...")
        self.group_entity = await find_or_join_group(self.client)
        if not self.group_entity:
            return False
        
        # Initialize OCR model
        self.logger.info("🤖 Initializing OCR model for math challenges...")
        self.ocr_model, self.ocr_executor = await initialize_ocr_model()
        if not self.ocr_model:
            self.logger.warning("⚠️  Failed to initialize OCR model, math challenge processing may not work")
        else:
            self.logger.info("✅ OCR model initialized successfully")
        
        # Register message event handler
        self.logger.info("📨 Registering message event handlers...")
        self.client.add_event_handler(
            lambda event: handle_new_message(event, self.client, self.group_entity, self.ocr_model, self.ocr_executor),
            events.NewMessage(chats=self.group_entity)
        )
        self.logger.info(f"✅ Message event handler registered for group: {self.group_entity.title}")
        if MESSAGE_SENDER_USERNAME:
            self.logger.info(f"   Filter: Only messages from @{MESSAGE_SENDER_USERNAME}")
        else:
            self.logger.info(f"   Filter: All senders")
        
        return True
    
    def _print_config_summary(self):
        """Print configuration summary."""
        from .config.settings import WORD_SENDER_SLOW_MODE, GROUP_NAME
        self.logger.info("📋 Configuration Summary:")
        self.logger.info(f"   • Word Sending: {'✅ Enabled' if ENABLE_WORD_SENDING else '❌ Disabled'}")
        if ENABLE_WORD_SENDING:
            mode = "Slow (100-150 msg/h)" if not WORD_SENDER_SLOW_MODE else "Fast (900-1100 msg/h)"
            self.logger.info(f"   • Word Sender Mode: {mode}")
            if AUTO_DELETE_WORD_MESSAGES:
                self.logger.info(f"   • Auto-Delete Word Messages: ✅ Enabled (deletes after 1s)")
            else:
                self.logger.info(f"   • Auto-Delete Word Messages: ❌ Disabled")
        if ENABLE_BONUS_MESSAGES:
            self.logger.info(f"   • Bonus Messages: ✅ Enabled (random interval: {BONUS_INTERVAL_MIN}-{BONUS_INTERVAL_MAX}s)")
        else:
            self.logger.info(f"   • Bonus Messages: ❌ Disabled")
        self.logger.info(f"   • Math Challenges: {'✅ Enabled' if ENABLE_MATH_CHALLENGES else '❌ Disabled'}")
        self.logger.info(f"   • Box Messages: {'✅ Enabled' if ENABLE_BOX_MESSAGES else '❌ Disabled'}")
        if MESSAGE_SENDER_USERNAME:
            self.logger.info(f"   • Message Filter: @{MESSAGE_SENDER_USERNAME}")
        else:
            self.logger.info(f"   • Message Filter: All senders")
        self.logger.info(f"   • Target Group: {GROUP_NAME or 'Auto-detect'}")
        self.logger.info("")
    
    async def start(self):
        """Start all bot services."""
        # Start worker thread
        self.logger.info("🔄 Starting message worker thread...")
        self.worker_thread = threading.Thread(
            target=message_worker,
            args=(self.message_queue, self.client, self.group_entity, self.event_loop, self.worker_running),
            daemon=True
        )
        self.worker_thread.start()
        self.logger.info("✅ Message worker thread started")
        
        # Start bonus message loop as async task (only if enabled)
        if ENABLE_BONUS_MESSAGES:
            self.logger.info(f"💬 Starting bonus message loop (random interval: {BONUS_INTERVAL_MIN}-{BONUS_INTERVAL_MAX}s)...")
            self.bonus_loop_task = asyncio.create_task(
                bonus_message_loop(self.client, self.group_entity, self.running)
            )
            self.logger.info("✅ Bonus message loop started")
        else:
            self.logger.info("⏭️  Bonus messages are disabled. Bonus message loop will not start.")
        
        # Start main loop in background (only if word sending is enabled)
        if ENABLE_WORD_SENDING:
            self.logger.info("📝 Starting word sending loop...")
            self.word_sender_task = asyncio.create_task(
                word_sender_loop(self.wordlist, self.message_queue, self.running)
            )
            self.logger.info("✅ Word sending loop started")
        else:
            self.logger.info("⏭️  Word sending is disabled. Main loop will not start.")
        
        # Print ready message
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("✅ Bot is now running and ready!")
        self.logger.info("=" * 60)
        self.logger.info("📊 Active Features:")
        if ENABLE_WORD_SENDING:
            self.logger.info("   • Word sending: ✅ Active")
        else:
            self.logger.info("   • Word sending: ❌ Disabled")
        if ENABLE_BONUS_MESSAGES:
            self.logger.info("   • Bonus messages: ✅ Active")
        else:
            self.logger.info("   • Bonus messages: ❌ Disabled")
        if ENABLE_MATH_CHALLENGES:
            self.logger.info("   • Math challenges: ✅ Active")
        else:
            self.logger.info("   • Math challenges: ❌ Disabled")
        if ENABLE_BOX_MESSAGES:
            self.logger.info("   • Box messages: ✅ Active")
        else:
            self.logger.info("   • Box messages: ❌ Disabled")
        self.logger.info("")
        self.logger.info("Press Ctrl+C to stop the bot")
        self.logger.info("=" * 60)
        self.logger.info("")
    
    async def run(self):
        """Run the bot until shutdown."""
        # Create shutdown event
        self.shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        setup_signal_handlers(self.shutdown_event, self.event_loop)
        
        try:
            # Keep running until interrupted
            await self.shutdown_event.wait()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except asyncio.CancelledError:
            self.logger.info("Tasks cancelled, shutting down...")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown all bot components."""
        self.running.clear()  # Signal all loops to stop
        self.worker_running.clear()  # Signal worker thread to stop
        self.shutdown_event.set()  # Signal shutdown
        
        # Cancel all running tasks
        self.logger.info("Cancelling running tasks...")
        tasks_to_cancel = []
        if self.bonus_loop_task:
            tasks_to_cancel.append(self.bonus_loop_task)
        if self.word_sender_task:
            tasks_to_cancel.append(self.word_sender_task)
        
        for task in tasks_to_cancel:
            task.cancel()
        
        # Wait for tasks to finish cancelling (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            self.logger.warning("Tasks did not cancel within timeout")
        except Exception as e:
            self.logger.debug(f"Error during task cancellation: {e}")
        
        # Signal worker thread to stop
        self.message_queue.put(None)  # Shutdown signal
        
        # Wait for worker thread to finish (with timeout)
        if self.worker_thread and self.worker_thread.is_alive():
            self.logger.info("Waiting for worker thread to finish...")
            self.worker_thread.join(timeout=2.0)
            if self.worker_thread.is_alive():
                self.logger.warning("Worker thread did not stop within timeout")
        
        # Shutdown OCR executor
        if self.ocr_executor:
            self.logger.info("🔄 Shutting down OCR executor...")
            self.ocr_executor.shutdown(wait=False)  # Don't wait, just shutdown
        
        if self.client:
            self.logger.info("🔌 Disconnecting Telegram client...")
            try:
                await asyncio.wait_for(self.client.disconnect(), timeout=2.0)
                self.logger.info("✅ Telegram client disconnected")
            except asyncio.TimeoutError:
                self.logger.warning("⚠️  Client disconnect timed out")
            except Exception as e:
                self.logger.debug(f"Error disconnecting client: {e}")
        
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("🛑 Bot stopped successfully")
        self.logger.info("=" * 60)


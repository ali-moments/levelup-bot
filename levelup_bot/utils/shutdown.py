"""Signal handling and graceful shutdown utilities."""

import asyncio
import logging
import signal
from typing import Optional

logger = logging.getLogger(__name__)


def setup_signal_handlers(shutdown_event: Optional[asyncio.Event], event_loop: Optional[asyncio.AbstractEventLoop]):
    """Setup signal handlers for graceful shutdown.
    
    Args:
        shutdown_event: Event to set when shutdown is requested
        event_loop: Async event loop to signal shutdown in
    """
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"🛑 Received shutdown signal ({signum})")
        logger.info("=" * 60)
        
        # Use the provided event_loop if available
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
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


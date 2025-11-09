#!/usr/bin/env python3
"""Schedule bonus messages using Telegram's scheduled message feature.

This script can be run once a day. It will:
1. Connect to Telegram
2. Find the target group
3. Schedule first message for 1 minute later
4. Schedule subsequent messages with random 3-5 minute intervals (cumulative)
5. Continue scheduling until 100 messages are scheduled (Telegram rate limit)
6. Exit immediately after scheduling (no waiting)

Usage:
    python schedule_bonus.py
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from telethon import errors

from levelup_bot.config.settings import BONUS_MESSAGE, BONUS_INTERVAL_MIN, BONUS_INTERVAL_MAX
from levelup_bot.config.logging_config import setup_logging
from levelup_bot.telegram.client import initialize_client
from levelup_bot.telegram.group import find_or_join_group

logger = logging.getLogger(__name__)


async def schedule_bonus_messages():
    """Schedule bonus messages using Telegram's scheduled message feature (max 100 messages)."""
    # Setup logging
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting bonus message scheduler (100 messages max)")
    logger.info("=" * 60)
    
    # Initialize client
    logger.info("Connecting to Telegram...")
    client = await initialize_client()
    if not client:
        logger.error("Failed to initialize Telegram client")
        return
    
    try:
        # Find or join group
        logger.info("Finding target group...")
        group_entity = await find_or_join_group(client)
        if not group_entity:
            logger.error("Failed to find or join target group")
            return
        
        logger.info(f"Target group: {group_entity.title} (ID: {group_entity.id})")
        
        # Calculate scheduling times
        now = datetime.now()
        base_time = now + timedelta(minutes=1)  # First message in 1 minute
        cumulative_time = timedelta(0)  # Start with 0 cumulative time
        max_messages = 100  # Telegram rate limit: maximum 100 scheduled messages
        
        message_count = 0
        scheduled_times = []
        
        logger.info("=" * 60)
        logger.info(f"Starting to schedule messages...")
        logger.info(f"Base time (first message): {base_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Maximum messages: {max_messages} (Telegram rate limit)")
        logger.info("=" * 60)
        
        # Schedule first message at base_time (1 minute later)
        first_schedule_time = base_time
        scheduled_times.append(first_schedule_time)
        message_count += 1
        
        try:
            await client.send_message(group_entity, BONUS_MESSAGE, schedule=first_schedule_time)
            logger.info(f"Message {message_count}: Scheduled for {first_schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except errors.FloodWaitError as e:
            logger.warning(f"Rate limited. Waiting {e.seconds} seconds before continuing...")
            await asyncio.sleep(e.seconds)
            await client.send_message(group_entity, BONUS_MESSAGE, schedule=first_schedule_time)
            logger.info(f"Message {message_count}: Scheduled for {first_schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error scheduling message {message_count}: {e}")
        
        # Schedule subsequent messages with cumulative random intervals
        # Stop at 100 messages (Telegram rate limit)
        while message_count < max_messages:
            # Generate random interval between 3-5 minutes
            random_interval_seconds = random.uniform(BONUS_INTERVAL_MIN, BONUS_INTERVAL_MAX)
            random_interval = timedelta(seconds=random_interval_seconds)
            
            # Add to cumulative time
            cumulative_time += random_interval
            
            # Calculate schedule time: base_time + cumulative_time
            schedule_time = base_time + cumulative_time
            scheduled_times.append(schedule_time)
            message_count += 1
            
            try:
                await client.send_message(group_entity, BONUS_MESSAGE, schedule=schedule_time)
                if message_count % 50 == 0:  # Log every 50 messages to avoid spam
                    logger.info(f"Message {message_count}: Scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} (cumulative: {cumulative_time.total_seconds()/3600:.2f} hours)")
            except errors.FloodWaitError as e:
                logger.warning(f"Rate limited. Waiting {e.seconds} seconds before continuing...")
                await asyncio.sleep(e.seconds)
                await client.send_message(group_entity, BONUS_MESSAGE, schedule=schedule_time)
                if message_count % 50 == 0:
                    logger.info(f"Message {message_count}: Scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} (cumulative: {cumulative_time.total_seconds()/3600:.2f} hours)")
            except Exception as e:
                logger.error(f"Error scheduling message {message_count}: {e}")
                # Continue with next message even if one fails
        
        # Summary
        logger.info("=" * 60)
        logger.info("Scheduling completed!")
        logger.info(f"Total messages scheduled: {message_count} (limit: {max_messages})")
        logger.info(f"First message: {scheduled_times[0].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Last message: {scheduled_times[-1].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total duration: {cumulative_time.total_seconds()/3600:.2f} hours")
        logger.info("=" * 60)
        logger.info("Script exiting. Messages will be sent automatically by Telegram.")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Error in scheduler: {e}", exc_info=True)
    finally:
        # Disconnect client
        if client and client.is_connected():
            logger.info("Disconnecting from Telegram...")
            await client.disconnect()
            logger.info("Disconnected")


def main():
    """Main entry point."""
    try:
        asyncio.run(schedule_bonus_messages())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()


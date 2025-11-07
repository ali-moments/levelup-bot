"""Configuration settings loaded from environment variables."""

from typing import Final, Optional
from dotenv import load_dotenv
import os

load_dotenv()

# Telegram API credentials
API_ID: Final[int] = int(os.getenv("API_ID", "YOUR_API_ID"))
API_HASH: Final[str] = os.getenv("API_HASH", "YOUR_API_HASH")
SESSION_NAME: Final[str] = os.getenv("SESSION_NAME", "YOUR_SESSION_NAME")

# Group settings
GROUP_INVITE_URL: Final[str] = os.getenv("GROUP_INVITE_URL", "https://t.me/+6p9Y15Lhw9I4ODFk")
GROUP_NAME: Final[str] = os.getenv("GROUP_NAME", "کودکسالان سیرک V.2")  # Optional: group name to find from dialogs

# Bonus message settings
BONUS_MESSAGE: Final[str] = "یا زهرا"
BONUS_INTERVAL_MIN: Final[int] = 181  # Minimum seconds between bonus messages (3 minutes + 1 second)
BONUS_INTERVAL_MAX: Final[int] = 300  # Maximum seconds between bonus messages (5 minutes)
# Note: BONUS_INTERVAL is kept for backward compatibility but will be replaced by random intervals
BONUS_INTERVAL: Final[int] = BONUS_INTERVAL_MIN  # Deprecated: use random interval between MIN and MAX

# Message handler settings
MESSAGE_SENDER_USERNAME: Final[Optional[str]] = os.getenv("MESSAGE_SENDER_USERNAME", "")  # Optional: only process messages from this username (empty = process all)

# Word sender settings
ENABLE_WORD_SENDING: Final[bool] = os.getenv("ENABLE_WORD_SENDING", "true").lower() in ("true", "1", "yes")  # Enable/disable word sending
WORD_SENDER_SLOW_MODE: Final[bool] = os.getenv("WORD_SENDER_SLOW_MODE", "true").lower() in ("false", "0", "no")  # If True: 900-1100 msg/h, If False: 100-150 msg/h
AUTO_DELETE_WORD_MESSAGES: Final[bool] = os.getenv("AUTO_DELETE_WORD_MESSAGES", "false").lower() in ("true", "1", "yes")  # Auto-delete word messages 1 second after sending

# Feature toggles
ENABLE_MATH_CHALLENGES: Final[bool] = os.getenv("ENABLE_MATH_CHALLENGES", "true").lower() in ("true", "1", "yes")  # Enable/disable math challenge processing
ENABLE_BOX_MESSAGES: Final[bool] = os.getenv("ENABLE_BOX_MESSAGES", "true").lower() in ("true", "1", "yes")  # Enable/disable box message processing
ENABLE_BONUS_MESSAGES: Final[bool] = os.getenv("ENABLE_BONUS_MESSAGES", "true").lower() in ("true", "1", "yes")  # Enable/disable bonus message sending

# Message rate based on WORD_SENDER setting
# If WORD_SENDER is True: 900-1100 messages/hour (3.27-4.0s delay)
# If WORD_SENDER is False: 100-150 messages/hour (24-36s delay)
# Note: If AUTO_DELETE_WORD_MESSAGES is enabled, we subtract 1 second from delays
# to account for the 1 second deletion wait time, maintaining the same effective rate
DELETE_WAIT_TIME: Final[float] = 1.0  # Seconds to wait before deleting message

if WORD_SENDER_SLOW_MODE:
    # 900 msg/h = 4.0s delay, 1100 msg/h = 3.27s delay
    base_min_delay = 3.27  # 1100 messages/hour
    base_max_delay = 4.0   # 900 messages/hour
else:
    # 100 msg/h = 36s delay, 150 msg/h = 24s delay
    base_min_delay = 24.0  # 150 messages/hour
    base_max_delay = 36.0  # 100 messages/hour

# Adjust delays if auto-delete is enabled (subtract deletion wait time)
if AUTO_DELETE_WORD_MESSAGES:
    MIN_MESSAGE_DELAY: Final[float] = max(0.1, base_min_delay - DELETE_WAIT_TIME)  # Ensure minimum 0.1s
    MAX_MESSAGE_DELAY: Final[float] = max(0.1, base_max_delay - DELETE_WAIT_TIME)  # Ensure minimum 0.1s
else:
    MIN_MESSAGE_DELAY: Final[float] = base_min_delay
    MAX_MESSAGE_DELAY: Final[float] = base_max_delay

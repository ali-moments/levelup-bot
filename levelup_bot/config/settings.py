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
BONUS_INTERVAL: Final[int] = 181  # Seconds between bonus messages (3 minutes + 1 second)

# Message handler settings
MESSAGE_SENDER_USERNAME: Final[Optional[str]] = os.getenv("MESSAGE_SENDER_USERNAME", "")  # Optional: only process messages from this username (empty = process all)

# Word sender settings
ENABLE_WORD_SENDING: Final[bool] = os.getenv("ENABLE_WORD_SENDING", "true").lower() in ("true", "1", "yes")  # Enable/disable word sending
WORD_SENDER_SLOW_MODE: Final[bool] = os.getenv("WORD_SENDER_SLOW_MODE", "true").lower() in ("false", "0", "no")  # If True: 900-1100 msg/h, If False: 100-150 msg/h

# Message rate based on WORD_SENDER setting
# If WORD_SENDER is True: 900-1100 messages/hour (3.27-4.0s delay)
# If WORD_SENDER is False: 100-150 messages/hour (24-36s delay)
if WORD_SENDER_SLOW_MODE:
    # 900 msg/h = 4.0s delay, 1100 msg/h = 3.27s delay
    MIN_MESSAGE_DELAY: Final[float] = 3.27  # 1100 messages/hour
    MAX_MESSAGE_DELAY: Final[float] = 4.0   # 900 messages/hour
else:
    # 100 msg/h = 36s delay, 150 msg/h = 24s delay
    MIN_MESSAGE_DELAY: Final[float] = 24.0  # 150 messages/hour
    MAX_MESSAGE_DELAY: Final[float] = 36.0  # 100 messages/hour

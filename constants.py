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
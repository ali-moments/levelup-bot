# LevelUp Bot

A Telegram bot that automatically sends messages to a group, processes math challenges using OCR, and interacts with inline buttons. The bot is designed to run continuously and handle various automated tasks in Telegram groups.

## Features

- **Automated Word Sending**: Sends random words from a wordlist to a Telegram group at configurable intervals
  - Fast mode: 900-1100 messages/hour (3.27-4.0s delay)
  - Slow mode: 100-150 messages/hour (24-36s delay)
- **Bonus Messages**: Sends periodic bonus messages with random intervals (3-5 minutes, 181-300 seconds)
- **Math Challenge Solver**: Automatically detects and solves math challenges from images using OCR
  - Downloads images from challenge messages
  - Extracts text using Pix2Text OCR
  - Parses and solves math expressions
  - Replies with the answer
- **Box Message Handler**: Automatically clicks all inline buttons in "box" messages
- **CPU-Only Mode**: Configured to run OCR operations on CPU only (no GPU required)

## Requirements

- Python 3.11+
- Telegram API credentials (API_ID and API_HASH)
- A Telegram account
- Access to the target Telegram group

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install telethon python-dotenv requests pillow pix2text
   ```

## Configuration

1. **Create a `.env` file** in the project root with the following variables:

   ```env
   # Telegram API credentials (required)
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   SESSION_NAME=levelup_bot

   # Group settings (at least one required)
   GROUP_INVITE_URL=https://t.me/+your_invite_link
   GROUP_NAME=Your Group Name  # Optional: used to find group by name

   # Bonus message settings
   BONUS_MESSAGE=یا زهرا  # Bonus message text (default: "یا زهرا")
   # Note: Bonus messages use random intervals (181-300 seconds, 3-5 minutes)

   # Message handler settings
   MESSAGE_SENDER_USERNAME=  # Optional: only process challenge/box messages from this username (empty = process all)

   # Word sender settings
   ENABLE_WORD_SENDING=true  # Enable/disable word sending (true/false)
   WORD_SENDER_SLOW_MODE=false  # false for fast mode (900-1100 msg/h), true for slow mode (100-150 msg/h)
   AUTO_DELETE_WORD_MESSAGES=false  # Auto-delete word messages 1 second after sending (true/false)
   ```

2. **Get Telegram API credentials**:
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy your `api_id` and `api_hash`

3. **Create a wordlist file** (only required if `ENABLE_WORD_SENDING=true`):
   - Create a file named `wordlist.txt` in the `data/` directory
   - Add one word per line (UTF-8 encoding)
   - Example:
     ```
     word1
     word2
     word3
     ```
   - Note: This file is only needed if word sending is enabled. If you disable word sending, you can skip this step.

## Usage

1. **Activate the virtual environment** (if using one):
   ```bash
   source venv/bin/activate
   ```

2. **Run the bot**:
   ```bash
   python main.py
   ```

3. **First run**: The bot will prompt you to authenticate with Telegram:
   - Enter your phone number
   - Enter the verification code sent to your Telegram account
   - If you have 2FA enabled, enter your password

4. **Stop the bot**: Press `Ctrl+C` to gracefully shutdown

### Scheduling Bonus Messages (Alternative)

Instead of running the bot continuously, you can use the `schedule_bonus.py` script to schedule bonus messages for 24 hours ahead using Telegram's native scheduled message feature:

```bash
python schedule_bonus.py
```

This script will:
- Schedule the first message 1 minute after running
- Schedule subsequent messages with random 3-5 minute intervals (cumulative)
- Continue scheduling until 100 messages are scheduled (Telegram rate limit)
- Exit immediately after scheduling (no waiting)

The messages will be sent automatically by Telegram at the scheduled times. Run this script once per day (or more frequently if you need more than 100 messages).

## How It Works

### Message Sending
- The bot can send random words from `wordlist.txt` to the configured group (can be disabled via `ENABLE_WORD_SENDING`)
- When enabled, message rate is controlled by `WORD_SENDER_SLOW_MODE` setting:
  - `false`: Fast mode (900-1100 messages/hour)
  - `true`: Slow mode (100-150 messages/hour)
- Messages are queued and processed by a worker thread to avoid blocking
- Set `ENABLE_WORD_SENDING=false` to disable word sending entirely (useful if you only want bonus messages, math challenges, or box handling)

### Bonus Messages
- Sends a bonus message (configurable via `BONUS_MESSAGE`) with random intervals
- Runs independently of word messages
- Interval: Random between 181-300 seconds (3-5 minutes) to avoid detection patterns
- Uses cryptographically secure randomization for unpredictability

### Math Challenge Processing
- Monitors messages in the target group (from all senders by default, or from a specific sender if `MESSAGE_SENDER_USERNAME` is set)
- Detects messages containing "چالش" (challenge) keyword or messages with photos
- Downloads images from challenge messages
- Uses OCR (Pix2Text) to extract text from images
- Parses math expressions and solves them
- Replies with the answer
- Set `MESSAGE_SENDER_USERNAME` in `.env` to only process messages from a specific bot/user

### Box Message Processing
- Detects messages containing "جعبه" (box) in the target group
- Automatically clicks all inline buttons in the message
- Handles various button types and structures
- Respects `MESSAGE_SENDER_USERNAME` setting if configured

## Project Structure

```
levelup_bot/
├── levelup_bot/          # Main package
│   ├── __init__.py
│   ├── main.py          # Package entry point
│   ├── bot.py           # Bot orchestrator
│   ├── config/          # Configuration module
│   ├── telegram/        # Telegram operations
│   ├── handlers/        # Message handlers
│   ├── services/        # Background services
│   ├── ocr/            # OCR functionality
│   └── utils/          # Utilities
├── docs/                # Documentation
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── CONFIGURATION.md
│   └── API.md
├── data/                # Data files
│   └── wordlist.txt    # Wordlist (create this file)
├── main.py             # Root entry point
├── schedule_bonus.py   # Script to schedule bonus messages for 24 hours
├── requirements.txt    # Python dependencies
├── setup.py           # Package setup
├── .env               # Environment variables (create this file)
└── README.md          # This file
```

For detailed documentation, see:
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [Architecture](docs/ARCHITECTURE.md) - Project architecture and design
- [Configuration](docs/CONFIGURATION.md) - Configuration reference
- [API Documentation](docs/API.md) - Internal API reference

## Technical Details

- **Async/Await**: Uses asyncio for non-blocking operations
- **Thread Pool**: OCR operations run in a thread pool to avoid blocking the event loop
- **CPU-Only OCR**: Configured to force CPU execution for ONNX Runtime (no GPU required)
- **Rate Limiting**: Handles Telegram rate limits automatically
- **Graceful Shutdown**: Properly handles SIGINT/SIGTERM signals for clean shutdown

## Troubleshooting

### Bot can't find the group
- Make sure `GROUP_NAME` matches the exact group name (case-insensitive)
- Or provide a valid `GROUP_INVITE_URL`
- Ensure you're a member of the group

### OCR not working
- The bot will continue running even if OCR initialization fails
- Math challenge processing will be disabled if OCR fails
- Check logs for OCR initialization errors

### Rate limiting
- The bot automatically handles Telegram rate limits
- If you see frequent rate limit warnings, consider using slow mode (`WORD_SENDER=false`)

### Session file issues
- If authentication fails, delete the `.session` file and restart
- The session file is created automatically on first run

## Notes

- The bot is designed to run continuously
- All operations are logged to the console
- The bot handles errors gracefully and continues running
- OCR model initialization may take some time on first run
- The bot monitors messages from a specific bot (`@`) for challenges

## License

This project is provided as-is for educational purposes.

## Disclaimer

This bot is designed for specific use cases. Make sure you comply with Telegram's Terms of Service and the rules of the groups you're using it in. Use responsibly.

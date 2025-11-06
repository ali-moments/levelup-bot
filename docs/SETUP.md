# Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- A Telegram account
- Telegram API credentials (API_ID and API_HASH)

## Step 1: Clone or Download

Clone the repository or download the project files to your local machine.

## Step 2: Create Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

Or install the package in development mode:

```bash
pip install -e .
```

## Step 4: Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy your `api_id` and `api_hash`

## Step 5: Configure Environment

1. Create a `.env` file in the project root:

```bash
cp .env.example .env  # If .env.example exists
# Or create .env manually
```

2. Edit `.env` and add your credentials:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_NAME=levelup_bot

# Group settings (at least one required)
GROUP_INVITE_URL=https://t.me/+your_invite_link
# OR
GROUP_NAME=Your Group Name

# Optional settings
BONUS_MESSAGE=یا زهرا
BONUS_INTERVAL=181
MESSAGE_SENDER_USERNAME=
ENABLE_WORD_SENDING=true
WORD_SENDER_SLOW_MODE=false
```

## Step 6: Prepare Wordlist (Optional)

If `ENABLE_WORD_SENDING=true`, create a wordlist file:

1. Create `data/wordlist.txt` (or use existing one)
2. Add one word per line (UTF-8 encoding)
3. Example:
   ```
   word1
   word2
   word3
   ```

## Step 7: Run the Bot

From the project root directory:

```bash
python main.py
```

Or if installed as a package:

```bash
levelup-bot
```

## First Run

On first run, the bot will prompt you to:
1. Enter your phone number
2. Enter the verification code sent to your Telegram account
3. Enter your 2FA password (if enabled)

A session file (`.session`) will be created for future runs.

## Troubleshooting

### Import Errors

If you see import errors, make sure you're running from the project root and the package is properly installed:

```bash
pip install -e .
```

### Module Not Found

Ensure you're in the project root directory and the virtual environment is activated.

### OCR Initialization Fails

The bot will continue running even if OCR fails. Math challenge processing will be disabled. Check logs for details.

### Group Not Found

- Verify `GROUP_NAME` matches exactly (case-insensitive)
- Or provide a valid `GROUP_INVITE_URL`
- Ensure you're a member of the group

### Session Issues

If authentication fails:
1. Delete the `.session` file
2. Restart the bot
3. Re-authenticate

## Development Setup

For development, install in editable mode:

```bash
pip install -e .
```

This allows code changes to be reflected without reinstalling.

## Production Deployment

For production:

1. Use a process manager (systemd, supervisor, etc.)
2. Set up proper logging
3. Use environment variables for configuration
4. Consider using a virtual environment
5. Set up auto-restart on failure

Example systemd service:

```ini
[Unit]
Description=LevelUp Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/levelup_bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```


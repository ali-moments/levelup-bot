# Configuration Reference

All configuration is done through environment variables, typically loaded from a `.env` file in the project root.

## Required Configuration

### Telegram API Credentials

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_NAME=levelup_bot
```

- **API_ID** and **API_HASH**: Get from https://my.telegram.org/apps
- **SESSION_NAME**: Name for the session file (default: `levelup_bot`)

## Group Configuration

At least one of the following is required:

```env
GROUP_INVITE_URL=https://t.me/+your_invite_link
GROUP_NAME=Your Group Name
```

- **GROUP_INVITE_URL**: Telegram group invite link
- **GROUP_NAME**: Exact group name (case-insensitive matching)

Priority:
1. Find by name (if `GROUP_NAME` is set)
2. Join via invite (if `GROUP_INVITE_URL` is set)
3. Use first group from dialogs (fallback)

## Message Sending Configuration

### Word Sending

```env
ENABLE_WORD_SENDING=true
WORD_SENDER_SLOW_MODE=false
```

- **ENABLE_WORD_SENDING**: Enable/disable word sending (`true`/`false`)
- **WORD_SENDER_SLOW_MODE**: 
  - `false`: Fast mode (900-1100 messages/hour, 3.27-4.0s delay)
  - `true`: Slow mode (100-150 messages/hour, 24-36s delay)

### Bonus Messages

```env
BONUS_MESSAGE=یا زهرا
BONUS_INTERVAL=181
```

- **BONUS_MESSAGE**: Text to send as bonus message
- **BONUS_INTERVAL**: Seconds between bonus messages (default: 181 = 3 minutes + 1 second)

## Message Filtering

```env
MESSAGE_SENDER_USERNAME=bot_username
```

- **MESSAGE_SENDER_USERNAME**: Only process challenge/box messages from this username
- Leave empty to process messages from all senders
- Username should not include the `@` symbol

## Configuration Examples

### Minimal Configuration

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=levelup_bot
GROUP_NAME=My Group
```

### Full Configuration

```env
# Telegram API
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=levelup_bot

# Group
GROUP_INVITE_URL=https://t.me/+abc123def456
GROUP_NAME=My Group Name

# Bonus Messages
BONUS_MESSAGE=یا زهرا
BONUS_INTERVAL=181

# Word Sending
ENABLE_WORD_SENDING=true
WORD_SENDER_SLOW_MODE=false

# Filtering
MESSAGE_SENDER_USERNAME=challenge_bot
```

### Word Sending Disabled

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=levelup_bot
GROUP_NAME=My Group
ENABLE_WORD_SENDING=false
```

This configuration will only send bonus messages and process challenges/boxes.

### Slow Mode Configuration

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=levelup_bot
GROUP_NAME=My Group
ENABLE_WORD_SENDING=true
WORD_SENDER_SLOW_MODE=true
```

This sends 100-150 messages/hour instead of 900-1100.

## Environment Variable Types

All variables are loaded as strings and converted to appropriate types:

- **API_ID**: Integer
- **API_HASH**: String
- **SESSION_NAME**: String
- **GROUP_INVITE_URL**: String
- **GROUP_NAME**: String
- **BONUS_MESSAGE**: String
- **BONUS_INTERVAL**: Integer (seconds)
- **MESSAGE_SENDER_USERNAME**: String (optional, can be empty)
- **ENABLE_WORD_SENDING**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)
- **WORD_SENDER_SLOW_MODE**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)

## Default Values

If a variable is not set, defaults are used:

- **SESSION_NAME**: `"YOUR_SESSION_NAME"`
- **GROUP_INVITE_URL**: `"https://t.me/+6p9Y15Lhw9I4ODFk"`
- **GROUP_NAME**: `"GROUP_NAME"`
- **BONUS_MESSAGE**: `"یا زهرا"`
- **BONUS_INTERVAL**: `181`
- **MESSAGE_SENDER_USERNAME**: `""` (empty, process all)
- **ENABLE_WORD_SENDING**: `true`
- **WORD_SENDER_SLOW_MODE**: `false` (fast mode)

## Validation

- Invalid values will use defaults or cause errors
- Missing required values (API_ID, API_HASH) will cause initialization to fail
- Invalid group configuration will prevent bot from starting

## Security Notes

- Never commit `.env` file to version control
- Keep API credentials secure
- Use different session names for different bots
- Session files contain authentication tokens - keep them secure


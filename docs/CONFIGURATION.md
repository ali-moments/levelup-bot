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
AUTO_DELETE_WORD_MESSAGES=false
```

- **ENABLE_WORD_SENDING**: Enable/disable word sending (`true`/`false`)
- **WORD_SENDER_SLOW_MODE**: 
  - `false`: Fast mode (900-1100 messages/hour, 3.27-4.0s delay)
  - `true`: Slow mode (100-150 messages/hour, 24-36s delay)
- **AUTO_DELETE_WORD_MESSAGES**: Auto-delete word messages 1 second after sending (`true`/`false`, default: `false`)
  - When enabled, word messages are automatically deleted 1 second after being sent
  - Message delays are automatically adjusted to maintain the same effective rate
  - Useful for keeping chat history clean while maintaining message rate

### Bonus Messages

```env
ENABLE_BONUS_MESSAGES=true
BONUS_MESSAGE=یا زهرا
```

- **ENABLE_BONUS_MESSAGES**: Enable/disable bonus message sending (`true`/`false`, default: `true`)
- **BONUS_MESSAGE**: Text to send as bonus message (default: `"یا زهرا"`)

**Note**: Bonus messages use random intervals between 3-5 minutes (181-300 seconds). The interval is randomly selected for each message to avoid detection patterns. The old `BONUS_INTERVAL` setting is deprecated and no longer used.

## Feature Toggles

```env
ENABLE_MATH_CHALLENGES=true
ENABLE_BOX_MESSAGES=true
```

- **ENABLE_MATH_CHALLENGES**: Enable/disable math challenge processing (`true`/`false`, default: `true`)
- **ENABLE_BOX_MESSAGES**: Enable/disable box message processing (`true`/`false`, default: `true`)

These settings control whether the bot will:
- Process and solve math challenges from images
- Automatically click inline buttons in box messages

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
ENABLE_BONUS_MESSAGES=true
BONUS_MESSAGE=یا زهرا
# Note: Bonus messages use random intervals (181-300 seconds, 3-5 minutes)

# Word Sending
ENABLE_WORD_SENDING=true
WORD_SENDER_SLOW_MODE=false
AUTO_DELETE_WORD_MESSAGES=false

# Feature Toggles
ENABLE_MATH_CHALLENGES=true
ENABLE_BOX_MESSAGES=true

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

This configuration will only send bonus messages and process challenges/boxes (if enabled).

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

### Disable Specific Features

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=levelup_bot
GROUP_NAME=My Group

# Disable math challenges and box messages, keep only word sending and bonus messages
ENABLE_MATH_CHALLENGES=false
ENABLE_BOX_MESSAGES=false
ENABLE_WORD_SENDING=true
ENABLE_BONUS_MESSAGES=true
```

This configuration will only send words and bonus messages, but won't process math challenges or box messages.

## Environment Variable Types

All variables are loaded as strings and converted to appropriate types:

- **API_ID**: Integer
- **API_HASH**: String
- **SESSION_NAME**: String
- **GROUP_INVITE_URL**: String
- **GROUP_NAME**: String
- **BONUS_MESSAGE**: String
- **MESSAGE_SENDER_USERNAME**: String (optional, can be empty)
- **ENABLE_WORD_SENDING**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)
- **WORD_SENDER_SLOW_MODE**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)
- **AUTO_DELETE_WORD_MESSAGES**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)
- **ENABLE_BONUS_MESSAGES**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)
- **ENABLE_MATH_CHALLENGES**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)
- **ENABLE_BOX_MESSAGES**: Boolean (`true`/`false`, `1`/`0`, `yes`/`no`)

## Default Values

If a variable is not set, defaults are used:

- **SESSION_NAME**: `"YOUR_SESSION_NAME"`
- **GROUP_INVITE_URL**: `"https://t.me/+6p9Y15Lhw9I4ODFk"`
- **GROUP_NAME**: `"GROUP_NAME"`
- **BONUS_MESSAGE**: `"یا زهرا"`
- **Bonus interval**: Random between 181-300 seconds (3-5 minutes)
- **MESSAGE_SENDER_USERNAME**: `""` (empty, process all)
- **ENABLE_WORD_SENDING**: `true`
- **WORD_SENDER_SLOW_MODE**: `false` (fast mode)
- **AUTO_DELETE_WORD_MESSAGES**: `false`
- **ENABLE_BONUS_MESSAGES**: `true`
- **ENABLE_MATH_CHALLENGES**: `true`
- **ENABLE_BOX_MESSAGES**: `true`

## Validation

- Invalid values will use defaults or cause errors
- Missing required values (API_ID, API_HASH) will cause initialization to fail
- Invalid group configuration will prevent bot from starting

## Security Notes

- Never commit `.env` file to version control
- Keep API credentials secure
- Use different session names for different bots
- Session files contain authentication tokens - keep them secure


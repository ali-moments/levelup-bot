# Architecture Documentation

## Overview

LevelUp Bot is structured as a modular Python package with clear separation of concerns. The architecture follows a layered design pattern with distinct modules for configuration, Telegram operations, message handling, background services, OCR processing, and utilities.

## Package Structure

```
levelup_bot/
├── __init__.py              # Package initialization
├── main.py                  # Simplified entry point (package-level)
├── bot.py                   # Main bot orchestrator class
├── config/                  # Configuration module
│   ├── __init__.py
│   ├── settings.py         # Environment-based settings
│   └── logging_config.py   # Logging configuration
├── telegram/                # Telegram client operations
│   ├── __init__.py
│   ├── client.py           # Client initialization
│   ├── group.py            # Group finding/joining
│   └── messaging.py        # Message sending
├── handlers/                # Message event handlers
│   ├── __init__.py
│   ├── message_handler.py  # Main message router
│   ├── math_challenge.py   # Math challenge processing
│   └── box_handler.py     # Box message processing
├── services/                # Background services
│   ├── __init__.py
│   ├── message_worker.py  # Queue worker thread
│   ├── word_sender.py     # Word sending service
│   └── bonus_sender.py    # Bonus message service
├── ocr/                     # OCR and math solving
│   ├── __init__.py
│   ├── cpu_patch.py       # ONNX Runtime CPU patching
│   ├── model.py           # OCR model initialization
│   └── math_solver.py    # Math expression parsing
└── utils/                   # Utility functions
    ├── __init__.py
    ├── wordlist.py        # Wordlist loading
    └── shutdown.py        # Signal handling
```

## Component Overview

### Bot Orchestrator (`bot.py`)

The `Bot` class is the central coordinator that:
- Manages the lifecycle of all components
- Handles initialization sequence
- Coordinates services and handlers
- Manages graceful shutdown

### Configuration Module (`config/`)

- **`settings.py`**: Loads all configuration from environment variables
- **`logging_config.py`**: Configures logging with appropriate levels

### Telegram Module (`telegram/`)

- **`client.py`**: Handles Telegram client initialization and connection
- **`group.py`**: Finds or joins target groups using various methods
- **`messaging.py`**: Provides functions for sending messages

### Handlers Module (`handlers/`)

- **`message_handler.py`**: Routes incoming messages to appropriate handlers
- **`math_challenge.py`**: Processes math challenge images using OCR
- **`box_handler.py`**: Handles box messages with inline buttons

### Services Module (`services/`)

- **`message_worker.py`**: Thread-based worker that processes message queue
- **`word_sender.py`**: Async service that sends random words
- **`bonus_sender.py`**: Async service that sends periodic bonus messages

### OCR Module (`ocr/`)

- **`cpu_patch.py`**: Patches ONNX Runtime to force CPU-only execution
- **`model.py`**: Initializes and manages OCR model
- **`math_solver.py`**: Parses and solves math expressions from text

### Utils Module (`utils/`)

- **`wordlist.py`**: Loads wordlist from file
- **`shutdown.py`**: Handles system signals for graceful shutdown

## Data Flow

### Message Sending Flow

1. **Word Sender Service** → Selects random word → Adds to message queue
2. **Message Worker Thread** → Processes queue → Sends via Telegram client
3. **Rate Limiting** → Enforced by delays between messages

### Message Receiving Flow

1. **Telegram Client** → Receives new message event
2. **Message Handler** → Routes to appropriate handler based on content
3. **Math Challenge Handler** → Downloads image → OCR → Solves → Replies
4. **Box Handler** → Clicks all inline buttons

### Bonus Message Flow

1. **Bonus Sender Service** → Waits for interval → Sends bonus message
2. **Independent Loop** → Runs separately from word sending

## Threading Model

- **Main Thread**: Runs asyncio event loop
- **Worker Thread**: Processes message queue (blocking operations)
- **OCR Executor**: Thread pool for OCR operations (2 workers)

## Async/Sync Boundaries

- **Async**: Telegram operations, message loops, event handling
- **Sync**: OCR operations (run in thread pool), queue processing
- **Bridge**: `asyncio.run_coroutine_threadsafe()` for thread→async communication

## Error Handling

- All modules use try/except with logging
- Graceful degradation (e.g., OCR failure doesn't stop bot)
- Proper cleanup in shutdown handlers

## Configuration Management

- All settings loaded from environment variables via `.env` file
- Settings are type-safe with Final annotations
- Default values provided for optional settings

## Extension Points

To add new features:

1. **New Handler**: Add to `handlers/` and register in `message_handler.py`
2. **New Service**: Add to `services/` and start in `bot.py`
3. **New Config**: Add to `config/settings.py`
4. **New Utility**: Add to `utils/`


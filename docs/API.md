# Internal API Documentation

This document describes the internal API of LevelUp Bot modules.

## Bot Orchestrator

### `Bot` Class

Main bot orchestrator that coordinates all components.

#### Methods

- `__init__()`: Initialize bot instance
- `initialize() -> bool`: Initialize all components, returns success status
- `start()`: Start all services
- `run()`: Run bot until shutdown
- `shutdown()`: Gracefully shutdown all components

## Configuration Module

### `config.settings`

Configuration constants loaded from environment variables.

#### Constants

- `API_ID`: Telegram API ID
- `API_HASH`: Telegram API hash
- `SESSION_NAME`: Session file name
- `GROUP_INVITE_URL`: Group invite URL
- `GROUP_NAME`: Group name
- `BONUS_MESSAGE`: Bonus message text
- `BONUS_INTERVAL`: Bonus message interval (seconds)
- `MESSAGE_SENDER_USERNAME`: Optional sender filter
- `ENABLE_WORD_SENDING`: Enable word sending flag
- `WORD_SENDER_SLOW_MODE`: Slow mode flag
- `MIN_MESSAGE_DELAY`: Minimum delay between messages
- `MAX_MESSAGE_DELAY`: Maximum delay between messages

### `config.logging_config`

#### Functions

- `setup_logging() -> logging.Logger`: Configure and return logger

## Telegram Module

### `telegram.client`

#### Functions

- `initialize_client() -> Optional[TelegramClient]`: Initialize and connect client

### `telegram.group`

#### Functions

- `find_group_by_name(client, group_name) -> Optional[Channel]`: Find group by name
- `join_group_via_invite(client, invite_url) -> Optional[Channel]`: Join group via invite
- `find_or_join_group(client) -> Optional[Channel]`: Find or join group using config

### `telegram.messaging`

#### Functions

- `send_message_to_group(client, group_entity, message) -> bool`: Send message to group
- `send_bonus_message(client, group_entity, bonus_message) -> bool`: Send bonus message

## Handlers Module

### `handlers.message_handler`

#### Functions

- `handle_new_message(event, client, group_entity, ocr_model, ocr_executor)`: Main message router

### `handlers.math_challenge`

#### Functions

- `process_math_challenge(client, message, ocr_model, ocr_executor)`: Process math challenge

### `handlers.box_handler`

#### Functions

- `process_box_message(message)`: Process box message with buttons

## Services Module

### `services.message_worker`

#### Functions

- `message_worker(message_queue, client, group_entity, event_loop, running_flag)`: Worker thread function

### `services.word_sender`

#### Functions

- `word_sender_loop(wordlist, message_queue, running_flag)`: Word sending async loop

### `services.bonus_sender`

#### Functions

- `bonus_message_loop(client, group_entity, running_flag)`: Bonus message async loop

## OCR Module

### `ocr.cpu_patch`

#### Functions

- `apply_cpu_patches() -> bool`: Apply ONNX Runtime CPU patches
- `ensure_cpu_patches() -> bool`: Ensure patches are applied

### `ocr.model`

#### Functions

- `initialize_ocr_model() -> tuple[Optional[Pix2Text], Optional[ThreadPoolExecutor]]`: Initialize OCR model

### `ocr.math_solver`

#### Functions

- `parse_and_solve_math(text) -> Optional[float]`: Parse and solve math expression

## Utils Module

### `utils.wordlist`

#### Functions

- `load_wordlist(filename="data/wordlist.txt") -> list[str]`: Load wordlist from file

### `utils.shutdown`

#### Functions

- `setup_signal_handlers(shutdown_event, event_loop)`: Setup signal handlers

## Type Hints

All functions use type hints for better IDE support and documentation:

- `Optional[T]`: Value can be `T` or `None`
- `Final[T]`: Immutable constant of type `T`
- `list[str]`: List of strings
- `tuple[T, U]`: Tuple with types T and U

## Async Functions

Functions marked with `async` must be awaited:

- All Telegram operations
- Service loops
- Bot lifecycle methods

## Thread Safety

- Message queue operations are thread-safe
- Event flags (`asyncio.Event`, `threading.Event`) are thread-safe
- Use `asyncio.run_coroutine_threadsafe()` for thread→async communication

## Error Handling

All functions:
- Log errors using the module logger
- Return `None` or `False` on failure
- Raise exceptions only for critical errors
- Use try/except blocks for graceful error handling

## Module Dependencies

```
bot.py
├── config/
│   ├── settings
│   └── logging_config
├── telegram/
│   ├── client
│   ├── group
│   └── messaging
├── handlers/
│   ├── message_handler
│   ├── math_challenge
│   └── box_handler
├── services/
│   ├── message_worker
│   ├── word_sender
│   └── bonus_sender
├── ocr/
│   ├── cpu_patch
│   ├── model
│   └── math_solver
└── utils/
    ├── wordlist
    └── shutdown
```


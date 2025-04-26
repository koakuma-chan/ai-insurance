# Claude Code Guidelines for Car Insurance Telegram Bot

This document contains instructions and information for Claude Code when working with this project.

## Project Overview

The Car Insurance Telegram Bot is a multi-agent application that guides users through the car insurance application process from document verification to policy issuance.

## Key Components

- **Telegram Bot Interface** - Uses the aiogram 3.x framework
- **AI Agents System** - Uses OpenAI's agents framework for specialized handling of different stages
- **Document Processing** - Uses Mindee AI for document data extraction
- **Database** - SQLite with WAL journaling for conversation persistence

## Project Structure

```
car-insurance-telegram-bot/
├── main.py                # Entry point with signal handling
├── requirements.txt       # Dependencies
├── example.env            # Environment variable template
├── assets/                # Static assets directory
│   └── examples/          # Example documents
│       ├── passport.png   # Sample passport document
│       └── vehicle id.png # Sample vehicle ID document
├── src/
│   ├── __init__.py        # Package metadata
│   ├── bot/               # Telegram bot interface
│   │   ├── __init__.py
│   │   ├── bot.py         # Bot service initialization
│   │   └── handlers.py    # Message handling
│   ├── config/            # Configuration
│   │   ├── __init__.py
│   │   └── settings.py    # Environment variables and constants
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── conversation.py # Conversation state
│   ├── services/          # Business logic
│   │   ├── __init__.py
│   │   ├── ai_service.py  # AI agent management
│   │   └── database.py    # Database interactions
│   └── utils/             # Utilities
│       ├── __init__.py
│       └── logging.py     # Logging configuration
```

## Coding Standards

When making changes to this codebase, follow these Python best practices:

1. **Type Hints**: Always include proper type annotations for function parameters and return values.

2. **Docstrings**: All modules, classes, and functions should have descriptive docstrings following the Google docstring format.

3. **Error Handling**: Use specific exception handling rather than general try/except blocks. Always log exceptions.

4. **Imports**: Use absolute imports from the project root. Import modules in this order: standard library, third-party, local application.

5. **Logging**: Use the logging utility in src/utils/logging.py rather than print statements.

6. **Documentation**: Keep README.md and CLAUDE.md up to date with any significant changes to the codebase, structure, or functionality.

## Commands to Run

When working on this project, use these commands:

### Running the Bot

```bash
python main.py
```

### Setting Up Environment

```bash
cp example.env .env
# Edit .env with appropriate API keys and settings
```

## Important Notes

1. **Environment Variables**: All configuration should be done through environment variables defined in .env file.

2. **Bot Authentication**: The project requires a Telegram Bot token, OpenAI API key, and Mindee API credentials.

3. **Database Operations**: The database connection is automatically closed on shutdown. New database operations should follow the patterns in database.py.

4. **Async Code**: This project uses asyncio extensively. Be careful with blocking operations.

5. **Media Handling**: The bot supports document uploads with specialized handling for media groups.

6. **External Services**: The bot interacts with:
   - Telegram Bot API
   - OpenAI API
   - Mindee API (for document data extraction)

## Security Considerations

1. Always validate user input before processing
2. Don't store sensitive information in logs
3. Use secure methods to handle API keys
4. Ensure proper error handling to prevent information leakage

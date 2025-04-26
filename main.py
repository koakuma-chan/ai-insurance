"""Entry point for the car insurance telegram bot application.

This script sets up logging, loads environment variables, and starts the bot service.
"""

import asyncio
import os
import signal
import sys
from typing import Any, Callable, Dict, Optional

from src.bot.bot import BotService
from src.config.settings import load_dotenv, DATA_DIRECTORY_PATH
from src.services.database import DatabaseService
from src.bot.handlers import MessageHandlers
from src.utils.logging import setup_logging, get_logger

# Load environment variables first to access logging configuration
load_dotenv()

# Set up logging
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", os.path.join(DATA_DIRECTORY_PATH, "bot.log"))

# Convert string log level to numeric value
LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
LOG_LEVEL = LOG_LEVELS.get(LOG_LEVEL_STR.upper(), 20)  # Default to INFO if invalid

setup_logging(
    log_level=LOG_LEVEL,
    log_file=LOG_FILE,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create logger for this module
logger = get_logger(__name__)


async def main() -> None:
    """Main async function that initializes and starts the bot service."""
    # Create bot service instance
    bot_service: Optional[BotService] = None

    try:
        logger.info("Initializing bot service")
        bot_service = BotService()

        # Start the bot
        logger.info("Starting the Car Insurance Telegram Bot")
        await bot_service.start()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        sys.exit(1)


def shutdown_handler(
    sig: int, frame: Any, cleanup_tasks: Dict[str, Callable] = None
) -> None:
    """Handle shutdown signals by cleaning up resources and exiting.

    Args:
        sig: Signal number
        frame: Current stack frame
        cleanup_tasks: Dictionary of cleanup functions to run before exit
    """
    signal_name = signal.Signals(sig).name
    logger.info(f"Received shutdown signal {signal_name} ({sig})")

    # Run cleanup tasks
    if cleanup_tasks:
        for task_name, task_func in cleanup_tasks.items():
            try:
                logger.info(f"Running cleanup task: {task_name}")
                task_func()
            except Exception as e:
                logger.error(f"Error in cleanup task {task_name}: {str(e)}")

    logger.info("Shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    # Create an instance of message handlers to get a reference for cleanup
    message_handlers = MessageHandlers()

    # Setup signal handlers for graceful shutdown
    cleanup_tasks = {
        "close_database": lambda: DatabaseService().close(),
        "cleanup_handlers": lambda: message_handlers.cleanup(),
    }

    signal.signal(
        signal.SIGINT, lambda sig, frame: shutdown_handler(sig, frame, cleanup_tasks)
    )
    signal.signal(
        signal.SIGTERM, lambda sig, frame: shutdown_handler(sig, frame, cleanup_tasks)
    )

    logger.info("Starting Car Insurance Telegram Bot application")
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)

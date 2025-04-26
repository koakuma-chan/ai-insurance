"""Bot service module for Telegram bot initialization and management.

This module provides the BotService class for initializing the Telegram bot,
registering message handlers, and starting the polling loop.
"""

import logging
from typing import List, Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from src.config.settings import BOT_TOKEN
from src.bot.handlers import MessageHandlers
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BotService:
    """Service for managing the Telegram bot.

    This class handles bot initialization, handler registration,
    and the main polling loop.

    Attributes:
        bot: The aiogram Bot instance
        dp: The aiogram Dispatcher instance
        handlers: The MessageHandlers instance
    """

    def __init__(self, token: Optional[str] = None) -> None:
        """Initialize the BotService.

        Args:
            token: Optional Telegram bot token. If not provided, BOT_TOKEN from
                  settings will be used.

        Raises:
            ValueError: If the token is invalid
        """
        try:
            # Initialize bot with markdown parsing
            self.bot = Bot(
                token=token or BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
            )

            # Create dispatcher
            self.dp = Dispatcher()

            # Initialize message handlers
            self.handlers = MessageHandlers()

            # Register message handler
            self.dp.message()(self.handlers.message_handler)

            logger.info("Bot service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing bot service: {str(e)}")
            raise

    async def start(self, allowed_updates: Optional[List[str]] = None) -> None:
        """Start the bot polling loop.

        Args:
            allowed_updates: List of update types to process. Defaults to ["message"].

        Raises:
            TelegramAPIError: If there's an error communicating with Telegram API
        """
        if allowed_updates is None:
            allowed_updates = ["message"]

        try:
            logger.info("Starting bot polling...")
            await self.dp.start_polling(
                self.bot, allowed_updates=allowed_updates, handle_as_tasks=True
            )
        except TelegramAPIError as e:
            logger.error(f"Telegram API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in bot polling: {str(e)}")
            raise

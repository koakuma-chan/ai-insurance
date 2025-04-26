"""Message handlers for the Telegram bot.

This module contains the MessageHandlers class that processes
incoming Telegram messages, including media group handling.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Callable, Any

from aiogram import Bot
from aiogram.enums.chat_action import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, User

from src.services.ai_service import AIService
from src.config.settings import MEDIA_GROUP_TIMEOUT
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MessageHandlers:
    """Handles incoming messages for the Telegram bot.

    This class manages message processing, including:
    - Single message handling
    - Media group collection and processing
    - Typing indicators during processing
    - Throttling to prevent concurrent processing for the same user

    Attributes:
        ai_service: The AI service for processing messages
        is_processing_map: Map of chat IDs to processing status
        media_groups: Map of media group IDs to collected messages
        media_group_locks: Locks for each media group to handle concurrent updates
    """

    def __init__(self) -> None:
        """Initialize the message handlers."""
        self.ai_service = AIService()
        self.is_processing_map: Dict[int, bool] = {}
        self.media_groups: Dict[str, List[Message]] = defaultdict(list)
        self.media_group_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Set to track active typing tasks so they can be cancelled
        self._active_typing_tasks: Dict[int, asyncio.Task] = {}

        logger.info("Message handlers initialized")

    async def _send_continuous_typing_action(self, bot: Bot, chat_id: int) -> None:
        """Continuously send typing action until cancelled.

        Args:
            bot: The Telegram bot instance
            chat_id: The chat ID to send typing indicators to
        """
        try:
            while True:
                try:
                    await bot.send_chat_action(
                        chat_id=chat_id, action=ChatAction.TYPING
                    )
                    await asyncio.sleep(3)
                except TelegramAPIError as e:
                    logger.warning(f"Error sending typing action: {str(e)}")
                    # If we can't send typing action, stop trying
                    break
                except asyncio.CancelledError:
                    # Task was cancelled, exit gracefully
                    break
        finally:
            # Remove task from tracking dict when complete
            if chat_id in self._active_typing_tasks:
                del self._active_typing_tasks[chat_id]

    async def process_message_batch(
        self, bot: Bot, user: User, messages: List[Message]
    ) -> None:
        """Process a batch of messages from the same user.

        Args:
            bot: The Telegram bot instance
            user: The user who sent the messages
            messages: List of messages to process
        """
        if not messages:
            logger.debug("Received empty message batch, ignoring")
            return

        chat_id = messages[0].chat.id

        # Ignore the new message if the previous one is still being processed
        is_processing = self.is_processing_map.get(chat_id, False)
        if is_processing:
            logger.debug(
                f"Chat {chat_id} is already being processed, ignoring new messages"
            )
            return

        logger.info(f"Processing {len(messages)} messages from chat {chat_id}")
        self.is_processing_map[chat_id] = True

        try:
            # Start typing indicator
            typing_task = asyncio.create_task(
                self._send_continuous_typing_action(bot, chat_id)
            )
            self._active_typing_tasks[chat_id] = typing_task

            try:
                # Wait for AI to respond
                await self.ai_service.respond(user=user, messages=messages)
            except Exception as e:
                logger.error(f"Error processing messages: {str(e)}")
                try:
                    # Notify user of error
                    await bot.send_message(
                        chat_id=chat_id,
                        text="Sorry, I encountered an error while processing your message. Please try again later.",
                    )
                except TelegramAPIError:
                    logger.error(f"Could not send error message to chat {chat_id}")

            # Cancel the typing action task
            if not typing_task.done():
                typing_task.cancel()

        finally:
            # Always mark as not processing, even if there was an error
            self.is_processing_map[chat_id] = False

            # Clean up any active typing task
            if (
                chat_id in self._active_typing_tasks
                and not self._active_typing_tasks[chat_id].done()
            ):
                self._active_typing_tasks[chat_id].cancel()

    async def message_handler(self, message: Message) -> None:
        """Handle a single incoming message.

        This is the main entry point called by the aiogram dispatcher.

        Args:
            message: The incoming Telegram message
        """
        user = message.from_user
        if user is None:
            logger.warning("Received message with no user, ignoring")
            return

        chat_id = message.chat.id
        media_group_id = message.media_group_id

        try:
            # If no media group, process immediately
            if not media_group_id:
                logger.debug(f"Processing single message from chat {chat_id}")
                await self.process_message_batch(message.bot, user, [message])
                return

            # Handle message as part of a media group
            logger.debug(f"Message belongs to media group {media_group_id}")
            await self._handle_media_group_message(message, user, media_group_id)
        except Exception as e:
            logger.error(f"Unhandled exception in message handler: {str(e)}")

    async def _handle_media_group_message(
        self, message: Message, user: User, media_group_id: str
    ) -> None:
        """Handle a message that is part of a media group.

        Args:
            message: The incoming message
            user: The user who sent the message
            media_group_id: The media group ID
        """
        # Add to media group and schedule processing
        async with self.media_group_locks[media_group_id]:
            # Add this message to the group
            self.media_groups[media_group_id].append(message)

            # If this is the first message in the group, schedule processing
            if len(self.media_groups[media_group_id]) == 1:
                logger.debug(
                    f"Scheduling processing for new media group {media_group_id}"
                )
                # Schedule a task to process this group after the timeout
                asyncio.create_task(
                    self.process_media_group(message.bot, user, media_group_id)
                )

    async def process_media_group(
        self, bot: Bot, user: User, media_group_id: str
    ) -> None:
        """Process all messages in a media group after a timeout.

        Args:
            bot: The Telegram bot instance
            user: The user who sent the messages
            media_group_id: The media group ID
        """
        try:
            # Wait for more messages in the same group
            logger.debug(
                f"Waiting {MEDIA_GROUP_TIMEOUT}s for media group {media_group_id} to complete"
            )
            await asyncio.sleep(MEDIA_GROUP_TIMEOUT)

            # Get all messages in this group
            async with self.media_group_locks[media_group_id]:
                if media_group_id not in self.media_groups:
                    logger.warning(
                        f"Media group {media_group_id} not found after timeout"
                    )
                    return

                messages = self.media_groups[media_group_id]
                # Sort by message ID to maintain order
                messages.sort(key=lambda msg: msg.message_id)

                # Clear the group
                del self.media_groups[media_group_id]

            logger.info(
                f"Processing media group {media_group_id} with {len(messages)} messages"
            )
            # Process the batch
            await self.process_message_batch(bot, user, messages)
        except Exception as e:
            logger.error(f"Error processing media group {media_group_id}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources used by the handler.

        This should be called when shutting down the bot.
        """
        # Cancel any active typing tasks
        for chat_id, task in self._active_typing_tasks.items():
            if not task.done():
                task.cancel()

        # Clean up media group data
        self.media_groups.clear()
        self.is_processing_map.clear()

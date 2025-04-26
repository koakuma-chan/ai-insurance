"""Models for conversation data and state.

This module contains data models related to conversation
history and state management.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union

# Reproduce the type from agents to avoid direct imports
# This mimics the structure while decoupling from the external package
TResponseInputItem = Dict[str, Any]


@dataclass
class ConversationHistory:
    """Represents the conversation history between a user and the bot.

    This class stores the conversational state, including the list of
    previous inputs and outputs, and the name of the last agent that
    processed the conversation.

    Attributes:
        input_list: A list of inputs and outputs from the conversation history
        last_agent_name: The name of the last agent that processed the conversation
    """

    input_list: List[TResponseInputItem]
    last_agent_name: str

    def __post_init__(self) -> None:
        """Validate the conversation history after initialization."""
        if not isinstance(self.input_list, list):
            raise TypeError("input_list must be a list")
        if not isinstance(self.last_agent_name, str):
            raise TypeError("last_agent_name must be a string")

    @property
    def is_empty(self) -> bool:
        """Check if the conversation history is empty.

        Returns:
            bool: True if the input list is empty, False otherwise
        """
        return len(self.input_list) == 0

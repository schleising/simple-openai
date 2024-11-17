"""Chat manager for the simple openai app

This module contains the chat manager for the simple openai app.

The chat manager is used to manage the chat messages and create the chat, it limits the number of messages in the chat to 21 by default and adds the system message to the start of the list.
"""

from collections import deque
from datetime import datetime
from pathlib import Path
import pickle
from zoneinfo import ZoneInfo

from .models import open_ai_models
from .constants import MAX_CHAT_HISTORY, CHAT_HISTORY_FILE, DEFAULT_CHAT_ID


class ChatManager:
    """The chat manager

    This class is used to manage the chat messages and create the chat, it limits the number of messages in the chat to 21 by default and adds the system message to the start of the list.

    It can optionally handle messages from multiple chats separately and store them in a file.

    On initialisation, the chat manager will try to load the chat history from the file.  If the file does not exist, it will create a new chat history.

    Args:
        system_message (str): The system message to add to the start of the chat
        max_messages (int, optional): The maximum number of messages in the chat. Defaults to 21.
        storage_path (Path, optional): The path to the storage directory. Defaults to None.
        timezone (str, optional): The timezone to use for the chat messages. Defaults to 'UTC'.
    """

    def __init__(
        self,
        system_message: str,
        max_messages: int = MAX_CHAT_HISTORY,
        storage_path: Path | None = None,
        timezone: str = "UTC",
    ) -> None:
        self._system_message = system_message
        self._max_messages = max_messages
        self._storage_path = storage_path
        self._timezone = ZoneInfo(timezone)

        # If a storage path is provided, create the storage directory
        if self._storage_path is not None:
            self._storage_path.mkdir(parents=True, exist_ok=True)

            # Try to load the chat history
            try:
                # Load the chat history
                with open(self._storage_path / CHAT_HISTORY_FILE, "rb") as f:
                    # Load the chat history
                    self._messages: dict[str, deque[open_ai_models.ChatMessage]] = (
                        pickle.load(f)
                    )
            except FileNotFoundError:
                # initialise a deque of messages not including the system message
                self._messages: dict[str, deque[open_ai_models.ChatMessage]] = {}
        else:
            # initialise a deque of messages not including the system message
            self._messages: dict[str, deque[open_ai_models.ChatMessage]] = {}

    def update_system_message(self, system_message: str) -> None:
        """Update the system message

        Args:
            system_message (str): The new system message
        """
        self._system_message = system_message

    def add_message(
        self,
        message: open_ai_models.ChatMessage,
        chat_id: str = DEFAULT_CHAT_ID,
        add_date_time: bool = False,
    ) -> open_ai_models.Chat:
        """Add a message to the chat

        Args:
            message (open_ai_models.ChatMessage): The message to add to the chat
            chat_id (str, optional): The ID of the chat to add the message to. Defaults to DEFAULT_CHAT_ID.
            add_date_time (bool, optional): Whether to add the date and time to the start of the prompt. Defaults to False.

        Returns:
            open_ai_models.Chat: The chat
        """
        # If the chat ID is not in the messages, create a new deque
        if chat_id not in self._messages:
            self._messages[chat_id] = deque(maxlen=self._max_messages)

        # Add the message to the deque
        self._messages[chat_id].append(message)

        # If a storage path is provided, save the chat history
        if self._storage_path is not None:
            # Save the chat history
            with open(self._storage_path / CHAT_HISTORY_FILE, "wb") as f:
                pickle.dump(self._messages, f)

        # Update the system message with the date and time in iso format if required
        if add_date_time:
            system_message = f"The date and time is {datetime.now(tz=self._timezone).isoformat()} give answers in timezone {self._timezone.key}.\n{self._system_message}"
        else:
            system_message = self._system_message

        # Create the chat adding the system message to the start
        chat = open_ai_models.Chat(
            messages=[
                open_ai_models.ChatMessage(
                    role="system", content=system_message, name="System"
                )
            ]
            + list(self._messages[chat_id])
        )

        # Return the chat
        return chat

    def get_chat(self, chat_id: str = DEFAULT_CHAT_ID) -> str:
        """Get the chat

        Args:
            chat_id (str, optional): The ID of the chat to get. Defaults to DEFAULT_CHAT_ID.

        Returns:
            str: The chat
        """
        # If the chat ID is not in the messages, create a new deque
        if chat_id not in self._messages:
            return ""

        # Get the chat
        chat = self._messages[chat_id]

        # Parse the most recent 10 chat messages to a string with each name and message on a new line
        chat_str = "\n".join([f"{message.name}: {message.content}" for message in chat])

        # Return the chat
        return chat_str

    def get_truncated_chat(self, chat_id: str = DEFAULT_CHAT_ID) -> str:
        """Get the truncated chat, limited to the last 4,000 characters

        Args:
            chat_id (str, optional): The ID of the chat to get. Defaults to DEFAULT_CHAT_ID.

        Returns:
            str: The truncated chat
        """
        # If the chat ID is not in the messages, create a new deque
        if chat_id not in self._messages:
            return ""

        # Get the chat
        chat = self._messages[chat_id]

        # Parse the most recent 10 chat messages to a string with each name and message on a new line
        chat_str = "\n".join([f"{message.name}: {message.content}" for message in chat])

        # Get the last 4,000 characters of the chat
        chat_str = chat_str[-4000:]

        # Return the chat
        return chat_str

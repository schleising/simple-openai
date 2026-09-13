"""Chat manager for the simple openai app

This module contains the chat manager for the simple openai app.

The chat manager is used to manage the chat messages and create the chat, it limits the number of messages in the chat to 21 by default and adds the system message to the start of the list.
"""

from collections import deque
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import open_ai_models
from .constants import MAX_CHAT_HISTORY, CHAT_HISTORY_FILE, DEFAULT_CHAT_ID

INCOMPLETE_TOOL_RESULT = "Tool call failed or did not complete."


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
                    self._chat_history = open_ai_models.ChatHistory.model_validate_json(
                        f.read()
                    )

                # Close any unanswered tool calls left behind by a previous failure
                repaired = False
                for chat_id in list(self._chat_history.messages):
                    if self._repair_chat(chat_id, close_trailing=True):
                        repaired = True

                if repaired:
                    self._save_history()
            except FileNotFoundError:
                # initialise a deque of messages not including the system message
                self._chat_history = open_ai_models.ChatHistory(messages={})
        else:
            # initialise a deque of messages not including the system message
            self._chat_history = open_ai_models.ChatHistory(messages={})

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

        Incomplete tool-call sequences are repaired before a non-tool message is
        added. OpenAI rejects a chat that has an assistant `tool_calls` message
        without a matching `tool` result for every `tool_call_id`.

        Args:
            message (open_ai_models.ChatMessage): The message to add to the chat
            chat_id (str, optional): The ID of the chat to add the message to. Defaults to DEFAULT_CHAT_ID.
            add_date_time (bool, optional): Whether to add the date and time to the start of the prompt. Defaults to False.

        Returns:
            open_ai_models.Chat: The chat
        """
        # If the chat ID is not in the chat history, create a new deque
        if chat_id not in self._chat_history.messages:
            self._chat_history.messages[chat_id] = deque(maxlen=self._max_messages)

        # Close unanswered tool calls before adding anything except a tool result.
        # A trailing assistant tool_calls message is left open when the next
        # message is a tool result so the real result can be recorded.
        if message.role != "tool":
            self._repair_chat(chat_id, close_trailing=True)

        # Add the message to the deque
        self._chat_history.messages[chat_id].append(message)

        # Drop tool results that lost their assistant tool_calls message when
        # the history was truncated.
        self._pop_orphaned_leading_tools(chat_id)

        # If a storage path is provided, save the chat history
        if self._storage_path is not None:
            self._save_history()

        # Return the chat
        return self._build_chat(chat_id, add_date_time)

    def get_chat(self, chat_id: str = DEFAULT_CHAT_ID) -> str:
        """Get the chat

        Args:
            chat_id (str, optional): The ID of the chat to get. Defaults to DEFAULT_CHAT_ID.

        Returns:
            str: The chat
        """
        # If the chat ID is not in the messages, create a new deque
        if chat_id not in self._chat_history.messages:
            return ""

        # Get the chat
        chat = self._chat_history.messages[chat_id]

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
        if chat_id not in self._chat_history.messages:
            return ""

        # Get the chat
        chat = self._chat_history.messages[chat_id]

        # Parse the most recent 10 chat messages to a string with each name and message on a new line
        chat_str = "\n".join([f"{message.name}: {message.content}" for message in chat])

        # Get the last 4,000 characters of the chat
        chat_str = chat_str[-4000:]

        # Return the chat
        return chat_str

    def clear_chat(self, chat_id: str = DEFAULT_CHAT_ID) -> None:
        """Clear the chat

        Args:
            chat_id (str, optional): The ID of the chat to clear. Defaults to DEFAULT_CHAT_ID.
        """
        # If the chat ID is not in the messages, create a new deque
        if chat_id not in self._chat_history.messages:
            return

        # Clear the chat
        self._chat_history.messages[chat_id].clear()

        # If a storage path is provided, save the chat history
        if self._storage_path is not None:
            self._save_history()

    def _save_history(self) -> None:
        """Save the chat history to disk"""
        if self._storage_path is None:
            return

        with open(self._storage_path / CHAT_HISTORY_FILE, "w") as f:
            f.write(self._chat_history.model_dump_json(exclude_none=True, indent=2))

    def _build_chat(self, chat_id: str, add_date_time: bool) -> open_ai_models.Chat:
        """Create a chat including the system message"""
        if add_date_time:
            system_message = (
                f"The date and time is {datetime.now(tz=self._timezone).isoformat()} "
                f"give answers in timezone {self._timezone.key}.\n{self._system_message}"
            )
        else:
            system_message = self._system_message

        return open_ai_models.Chat(
            messages=[
                open_ai_models.ChatMessage(
                    role="system", content=system_message, name="System"
                )
            ]
            + list(self._chat_history.messages[chat_id])
        )

    def _pop_orphaned_leading_tools(self, chat_id: str) -> None:
        """Remove tool results that are no longer attached to a tool call"""
        messages = self._chat_history.messages[chat_id]
        while messages and messages[0].role == "tool":
            messages.popleft()

    def _tool_result_message(self, tool_call_id: str) -> open_ai_models.ChatMessage:
        """Create a placeholder tool result for an unanswered tool call"""
        return open_ai_models.ChatMessage(
            role="tool",
            tool_call_id=tool_call_id,
            content=INCOMPLETE_TOOL_RESULT,
            name="Botto",
        )

    def _close_unanswered_tool_calls(
        self,
        messages: list[open_ai_models.ChatMessage],
        *,
        close_trailing: bool,
    ) -> list[open_ai_models.ChatMessage]:
        """Insert tool results for assistant tool_calls that were never answered

        A trailing assistant message with no tool results is left unchanged when
        `close_trailing` is False, so a real tool result can still be added.
        """
        repaired: list[open_ai_models.ChatMessage] = []
        index = 0

        while index < len(messages):
            message = messages[index]

            # Drop tool results that do not follow an assistant tool call
            if message.role == "tool":
                index += 1
                continue

            repaired.append(message)

            if message.role != "assistant" or not message.tool_calls:
                index += 1
                continue

            expected_ids = [tool_call.id for tool_call in message.tool_calls]
            answered_ids: set[str] = set()
            next_index = index + 1

            while next_index < len(messages) and messages[next_index].role == "tool":
                tool_message = messages[next_index]
                repaired.append(tool_message)
                if tool_message.tool_call_id is not None:
                    answered_ids.add(tool_message.tool_call_id)
                next_index += 1

            is_trailing = next_index >= len(messages)
            should_close = (not is_trailing) or close_trailing or bool(answered_ids)

            if should_close:
                for tool_call_id in expected_ids:
                    if tool_call_id not in answered_ids:
                        repaired.append(self._tool_result_message(tool_call_id))

            index = next_index

        return repaired

    def _repair_chat(self, chat_id: str, *, close_trailing: bool) -> bool:
        """Repair incomplete tool-call sequences in a chat

        Returns:
            bool: True if the stored messages were changed
        """
        if chat_id not in self._chat_history.messages:
            return False

        current_messages = list(self._chat_history.messages[chat_id])
        repaired_messages = self._close_unanswered_tool_calls(
            current_messages, close_trailing=close_trailing
        )

        if repaired_messages == current_messages:
            return False

        self._chat_history.messages[chat_id] = deque(
            repaired_messages, maxlen=self._max_messages
        )
        self._pop_orphaned_leading_tools(chat_id)
        return True

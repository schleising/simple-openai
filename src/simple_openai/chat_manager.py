"""Chat manager for the simple openai app

This module contains the chat manager for the simple openai app.

The chat manager stores a rolling window of Responses input items per chat,
caps it at 21 items by default, and builds the next request from that local
transcript. OpenAI does not retain the conversation (`store` is false).
"""

from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .models import open_ai_models
from .constants import (
    FUNCTION_CALL_OUTPUT_TYPE,
    FUNCTION_CALL_TYPE,
    MAX_CHAT_HISTORY,
    CHAT_HISTORY_FILE,
    DEFAULT_CHAT_ID,
    MESSAGE_TYPE,
)

INCOMPLETE_TOOL_RESULT = "Tool call failed or did not complete."


class ChatManager:
    """The chat manager

    This class is used to manage the chat items and create the next Responses
    request. It limits the number of items in the chat to 21 by default.

    It can optionally handle items from multiple chats separately and store
    them in a file.

    On initialisation, the chat manager will try to load the chat history from
    the file. If the file does not exist, it will create a new chat history.
    Older Chat Completions history files are converted to Responses items.

    Args:
        system_message (str): The system message sent as Responses `instructions`
        max_messages (int, optional): The maximum number of items in the chat. Defaults to 21.
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

                # Close any unanswered function calls left behind by a previous failure
                repaired = False
                for chat_id in list(self._chat_history.messages):
                    if self._repair_chat(chat_id, close_trailing=True):
                        repaired = True

                if repaired:
                    self._save_history()
            except FileNotFoundError:
                self._chat_history = open_ai_models.ChatHistory(messages={})
        else:
            self._chat_history = open_ai_models.ChatHistory(messages={})

    def update_system_message(self, system_message: str) -> None:
        """Update the system message

        Args:
            system_message (str): The new system message
        """
        self._system_message = system_message

    def add_item(
        self,
        item: open_ai_models.InputItem,
        chat_id: str = DEFAULT_CHAT_ID,
        add_date_time: bool = False,
    ) -> open_ai_models.ChatContext:
        """Add a single item to the chat"""
        return self.add_items([item], chat_id=chat_id, add_date_time=add_date_time)

    def add_items(
        self,
        items: list[open_ai_models.InputItem],
        chat_id: str = DEFAULT_CHAT_ID,
        add_date_time: bool = False,
    ) -> open_ai_models.ChatContext:
        """Add items to the chat

        Incomplete function-call sequences are repaired before a user or
        assistant message is added. OpenAI rejects input that has a
        `function_call` without a matching `function_call_output` for every
        `call_id`.

        Args:
            items (list[InputItem]): The items to add to the chat
            chat_id (str, optional): The ID of the chat to add the items to. Defaults to DEFAULT_CHAT_ID.
            add_date_time (bool, optional): Whether to add the date and time to the instructions. Defaults to False.

        Returns:
            open_ai_models.ChatContext: The instructions and input for the next request
        """
        if not items:
            return self._build_context(chat_id, add_date_time)

        # If the chat ID is not in the chat history, create a new deque
        if chat_id not in self._chat_history.messages:
            self._chat_history.messages[chat_id] = deque(maxlen=self._max_messages)

        # Close unanswered function calls before adding a new user/assistant turn.
        if self._should_close_before(items):
            self._repair_chat(chat_id, close_trailing=True)

        for item in items:
            self._chat_history.messages[chat_id].append(item)

        # Drop function-call outputs that lost their function_call when the
        # history was truncated.
        self._pop_orphaned_leading_outputs(chat_id)

        # If a storage path is provided, save the chat history
        if self._storage_path is not None:
            self._save_history()

        return self._build_context(chat_id, add_date_time)

    def add_user_message(
        self,
        prompt: str,
        name: str,
        chat_id: str = DEFAULT_CHAT_ID,
        add_date_time: bool = False,
    ) -> open_ai_models.ChatContext:
        """Add a user message to the chat"""
        return self.add_item(
            open_ai_models.InputItem(
                type=MESSAGE_TYPE,
                role="user",
                content=prompt,
                speaker=name,
            ),
            chat_id=chat_id,
            add_date_time=add_date_time,
        )

    def add_function_call_output(
        self,
        call_id: str,
        output: str,
        chat_id: str = DEFAULT_CHAT_ID,
        add_date_time: bool = False,
    ) -> open_ai_models.ChatContext:
        """Add a function-call result to the chat"""
        return self.add_item(
            open_ai_models.InputItem(
                type=FUNCTION_CALL_OUTPUT_TYPE,
                call_id=call_id,
                output=output,
            ),
            chat_id=chat_id,
            add_date_time=add_date_time,
        )

    def build_request(
        self,
        tools: list[open_ai_models.ResponsesFunctionTool] | None,
        *,
        chat_id: str,
        add_date_time: bool,
        allow_tool_calls: bool,
    ) -> dict[str, Any]:
        """Build a Responses request body from the local transcript"""
        context = self._build_context(chat_id, add_date_time)
        request = open_ai_models.ResponsesRequest(
            instructions=context.instructions,
            input=context.input,
            tools=tools,
            tool_choice=("auto" if allow_tool_calls else "none") if tools else None,
            parallel_tool_calls=False if tools else None,
        )
        return request.model_dump(exclude_none=True)

    def get_chat(self, chat_id: str = DEFAULT_CHAT_ID) -> str:
        """Get the chat

        Args:
            chat_id (str, optional): The ID of the chat to get. Defaults to DEFAULT_CHAT_ID.

        Returns:
            str: The chat
        """
        return self._render_chat(chat_id)

    def get_truncated_chat(self, chat_id: str = DEFAULT_CHAT_ID) -> str:
        """Get the truncated chat, limited to the last 4,000 characters

        Args:
            chat_id (str, optional): The ID of the chat to get. Defaults to DEFAULT_CHAT_ID.

        Returns:
            str: The truncated chat
        """
        return self._render_chat(chat_id)[-4000:]

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

    def _render_chat(self, chat_id: str) -> str:
        if chat_id not in self._chat_history.messages:
            return ""

        lines: list[str] = []
        for item in self._chat_history.messages[chat_id]:
            text = item.display_text()
            if text is None:
                continue
            lines.append(f"{item.display_name()}: {text}")
        return "\n".join(lines)

    def _save_history(self) -> None:
        """Save the chat history to disk"""
        if self._storage_path is None:
            return

        with open(self._storage_path / CHAT_HISTORY_FILE, "w") as f:
            f.write(self._chat_history.model_dump_json(exclude_none=True, indent=2))

    def _build_context(
        self, chat_id: str, add_date_time: bool
    ) -> open_ai_models.ChatContext:
        """Create instructions and API input from the local transcript"""
        if add_date_time:
            instructions = (
                f"The date and time is {datetime.now(tz=self._timezone).isoformat()} "
                f"give answers in timezone {self._timezone.key}.\n{self._system_message}"
            )
        else:
            instructions = self._system_message

        items = list(self._chat_history.messages.get(chat_id, ()))
        return open_ai_models.ChatContext(
            instructions=instructions,
            input=[item.to_api_payload() for item in items],
        )

    def _should_close_before(self, items: list[open_ai_models.InputItem]) -> bool:
        """Whether unanswered function calls should be closed before these items"""
        for item in items:
            if item.type in {
                FUNCTION_CALL_TYPE,
                FUNCTION_CALL_OUTPUT_TYPE,
                "reasoning",
            }:
                return False
        return True

    def _pop_orphaned_leading_outputs(self, chat_id: str) -> None:
        """Remove function-call outputs that are no longer attached to a call"""
        messages = self._chat_history.messages[chat_id]
        while messages and messages[0].type == FUNCTION_CALL_OUTPUT_TYPE:
            messages.popleft()

    def _tool_result_item(self, call_id: str) -> open_ai_models.InputItem:
        """Create a placeholder result for an unanswered function call"""
        return open_ai_models.InputItem(
            type=FUNCTION_CALL_OUTPUT_TYPE,
            call_id=call_id,
            output=INCOMPLETE_TOOL_RESULT,
        )

    def _close_unanswered_function_calls(
        self,
        items: list[open_ai_models.InputItem],
        *,
        close_trailing: bool,
    ) -> list[open_ai_models.InputItem]:
        """Insert function_call_output items for function_call items that were never answered"""
        repaired: list[open_ai_models.InputItem] = []
        unanswered: dict[str, None] = {}

        def close_unanswered() -> None:
            for call_id in list(unanswered):
                repaired.append(self._tool_result_item(call_id))
            unanswered.clear()

        for index, item in enumerate(items):
            is_last = index == len(items) - 1

            if item.type == FUNCTION_CALL_OUTPUT_TYPE:
                if item.call_id in unanswered:
                    repaired.append(item)
                    del unanswered[item.call_id]
                continue

            if item.type == FUNCTION_CALL_TYPE:
                if item.call_id is not None:
                    unanswered[item.call_id] = None
                repaired.append(item)
                continue

            should_close = (not is_last) or close_trailing or bool(unanswered)
            if item.type == MESSAGE_TYPE and item.role == "user" and unanswered:
                if should_close or not is_last:
                    close_unanswered()
            elif unanswered and item.type == MESSAGE_TYPE and item.role != "user":
                if close_trailing or not is_last:
                    close_unanswered()

            repaired.append(item)

        if close_trailing:
            close_unanswered()

        return repaired

    def _repair_chat(self, chat_id: str, *, close_trailing: bool) -> bool:
        """Repair incomplete function-call sequences in a chat

        Returns:
            bool: True if the stored items were changed
        """
        if chat_id not in self._chat_history.messages:
            return False

        current_items = list(self._chat_history.messages[chat_id])
        repaired_items = self._close_unanswered_function_calls(
            current_items, close_trailing=close_trailing
        )

        if repaired_items == current_items:
            return False

        self._chat_history.messages[chat_id] = deque(
            repaired_items, maxlen=self._max_messages
        )
        self._pop_orphaned_leading_outputs(chat_id)
        return True

import json
import tempfile
import unittest
from pathlib import Path

from simple_openai.chat_manager import INCOMPLETE_TOOL_RESULT, ChatManager
from simple_openai.constants import CHAT_HISTORY_FILE
from simple_openai.models import open_ai_models


def _tool_call(call_id: str, name: str = "internet_search") -> open_ai_models.ToolCall:
    return open_ai_models.ToolCall(
        id=call_id,
        type="function",
        function=open_ai_models.FunctionCall(
            name=name,
            arguments='{"query": "test"}',
        ),
    )


def _assistant_tool_call(call_id: str) -> open_ai_models.ChatMessage:
    return open_ai_models.ChatMessage(
        role="assistant",
        tool_calls=[_tool_call(call_id)],
        name="Botto",
    )


def _tool_result(call_id: str, content: str = "ok") -> open_ai_models.ChatMessage:
    return open_ai_models.ChatMessage(
        role="tool",
        tool_call_id=call_id,
        content=content,
        name="Botto",
    )


def _user_message(content: str) -> open_ai_models.ChatMessage:
    return open_ai_models.ChatMessage(role="user", content=content, name="Stephen")


class ChatManagerToolHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = ChatManager("You are a test assistant.")

    def test_unanswered_tool_call_is_closed_before_next_user_message(self) -> None:
        self.chat.add_message(_assistant_tool_call("call_1"))
        chat = self.chat.add_message(_user_message("Hello...?"))

        messages = [message for message in chat.messages if message.role != "system"]
        self.assertEqual(
            [message.role for message in messages],
            ["assistant", "tool", "user"],
        )
        self.assertEqual(messages[1].tool_call_id, "call_1")
        self.assertEqual(messages[1].content, INCOMPLETE_TOOL_RESULT)

    def test_complete_tool_sequence_is_left_alone(self) -> None:
        self.chat.add_message(_assistant_tool_call("call_1"))
        self.chat.add_message(_tool_result("call_1", "search results"))
        self.chat.add_message(
            open_ai_models.ChatMessage(
                role="assistant", content="Here you go", name="Botto"
            )
        )

        chat = self.chat.add_message(_user_message("Thanks"))
        messages = [message for message in chat.messages if message.role != "system"]
        self.assertEqual(
            [message.role for message in messages],
            ["assistant", "tool", "assistant", "user"],
        )
        self.assertEqual(messages[1].content, "search results")

    def test_real_tool_result_can_follow_an_open_tool_call(self) -> None:
        self.chat.add_message(_assistant_tool_call("call_1"))
        chat = self.chat.add_message(_tool_result("call_1", "search results"))

        messages = [message for message in chat.messages if message.role != "system"]
        self.assertEqual([message.role for message in messages], ["assistant", "tool"])
        self.assertEqual(messages[1].content, "search results")

    def test_missing_tool_result_is_inserted_before_later_user_message(self) -> None:
        self.chat.add_message(_assistant_tool_call("call_1"))
        self.chat._chat_history.messages["default"].append(_user_message("Hello...?"))

        chat = self.chat.add_message(_user_message("Are you there?"))
        messages = [message for message in chat.messages if message.role != "system"]
        self.assertEqual(
            [message.role for message in messages],
            ["assistant", "tool", "user", "user"],
        )
        self.assertEqual(messages[1].tool_call_id, "call_1")

    def test_partial_parallel_tool_results_are_completed(self) -> None:
        self.chat.add_message(
            open_ai_models.ChatMessage(
                role="assistant",
                tool_calls=[_tool_call("call_1"), _tool_call("call_2")],
                name="Botto",
            )
        )
        self.chat.add_message(_tool_result("call_1", "first result"))

        chat = self.chat.add_message(_user_message("Hello...?"))
        messages = [message for message in chat.messages if message.role != "system"]
        self.assertEqual(
            [message.role for message in messages],
            ["assistant", "tool", "tool", "user"],
        )
        self.assertEqual(messages[1].tool_call_id, "call_1")
        self.assertEqual(messages[2].tool_call_id, "call_2")
        self.assertEqual(messages[2].content, INCOMPLETE_TOOL_RESULT)

    def test_leading_orphaned_tool_results_are_removed(self) -> None:
        short_chat = ChatManager("You are a test assistant.", max_messages=2)
        short_chat.add_message(_assistant_tool_call("call_1"))
        short_chat.add_message(_tool_result("call_1"))
        short_chat.add_message(_user_message("next"))

        remaining = list(short_chat._chat_history.messages["default"])
        self.assertEqual([message.role for message in remaining], ["user"])

    def test_broken_history_is_repaired_on_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir)
            history = open_ai_models.ChatHistory(
                messages={
                    "-417681459": [
                        _user_message(
                            "A top safety researcher at Anthropic has warned AI..."
                        ),
                        _assistant_tool_call("call_Yj6AZxSRdNNmju6S1r8Ja7Xy"),
                        _user_message("Hello...?"),
                    ]
                }
            )
            (storage_path / CHAT_HISTORY_FILE).write_text(
                history.model_dump_json(exclude_none=True, indent=2)
            )

            ChatManager("You are a test assistant.", storage_path=storage_path)

            saved = json.loads((storage_path / CHAT_HISTORY_FILE).read_text())
            messages = saved["messages"]["-417681459"]
            self.assertEqual(
                [message["role"] for message in messages],
                ["user", "assistant", "tool", "user"],
            )
            self.assertEqual(
                messages[2]["tool_call_id"],
                "call_Yj6AZxSRdNNmju6S1r8Ja7Xy",
            )
            self.assertEqual(messages[2]["content"], INCOMPLETE_TOOL_RESULT)


if __name__ == "__main__":
    unittest.main()

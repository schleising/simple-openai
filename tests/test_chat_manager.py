import json
import tempfile
import unittest
from pathlib import Path

from simple_openai.chat_manager import INCOMPLETE_TOOL_RESULT, ChatManager
from simple_openai.constants import CHAT_HISTORY_FILE, FUNCTION_CALL_OUTPUT_TYPE, FUNCTION_CALL_TYPE, MESSAGE_TYPE
from simple_openai.models import open_ai_models


def _function_call(call_id: str, name: str = "internet_search") -> open_ai_models.InputItem:
    return open_ai_models.InputItem(
        type=FUNCTION_CALL_TYPE,
        call_id=call_id,
        name=name,
        arguments='{"query": "test"}',
    )


def _function_output(call_id: str, output: str = "ok") -> open_ai_models.InputItem:
    return open_ai_models.InputItem(
        type=FUNCTION_CALL_OUTPUT_TYPE,
        call_id=call_id,
        output=output,
    )


def _user_message(content: str) -> open_ai_models.InputItem:
    return open_ai_models.InputItem(
        type=MESSAGE_TYPE,
        role="user",
        content=content,
        speaker="Stephen",
    )


def _assistant_message(content: str) -> open_ai_models.InputItem:
    return open_ai_models.InputItem(
        type=MESSAGE_TYPE,
        role="assistant",
        content=content,
        speaker="Botto",
    )


def _item_types(context: open_ai_models.ChatContext) -> list[str]:
    return [str(item.get("type")) for item in context.input]


class ChatManagerToolHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chat = ChatManager("You are a test assistant.")

    def test_unanswered_function_call_is_closed_before_next_user_message(self) -> None:
        self.chat.add_item(_function_call("call_1"))
        context = self.chat.add_item(_user_message("Hello...?"))

        self.assertEqual(
            _item_types(context),
            [FUNCTION_CALL_TYPE, FUNCTION_CALL_OUTPUT_TYPE, MESSAGE_TYPE],
        )
        self.assertEqual(context.input[1]["call_id"], "call_1")
        self.assertEqual(context.input[1]["output"], INCOMPLETE_TOOL_RESULT)
        self.assertEqual(context.input[2]["content"], "Stephen: Hello...?")

    def test_complete_tool_sequence_is_left_alone(self) -> None:
        self.chat.add_item(_function_call("call_1"))
        self.chat.add_item(_function_output("call_1", "search results"))
        self.chat.add_item(_assistant_message("Here you go"))

        context = self.chat.add_item(_user_message("Thanks"))
        self.assertEqual(
            _item_types(context),
            [
                FUNCTION_CALL_TYPE,
                FUNCTION_CALL_OUTPUT_TYPE,
                MESSAGE_TYPE,
                MESSAGE_TYPE,
            ],
        )
        self.assertEqual(context.input[1]["output"], "search results")

    def test_real_tool_result_can_follow_an_open_function_call(self) -> None:
        self.chat.add_item(_function_call("call_1"))
        context = self.chat.add_item(_function_output("call_1", "search results"))

        self.assertEqual(
            _item_types(context),
            [FUNCTION_CALL_TYPE, FUNCTION_CALL_OUTPUT_TYPE],
        )
        self.assertEqual(context.input[1]["output"], "search results")

    def test_missing_tool_result_is_inserted_before_later_user_message(self) -> None:
        self.chat.add_item(_function_call("call_1"))
        self.chat._chat_history.messages["default"].append(_user_message("Hello...?"))

        context = self.chat.add_item(_user_message("Are you there?"))
        self.assertEqual(
            _item_types(context),
            [
                FUNCTION_CALL_TYPE,
                FUNCTION_CALL_OUTPUT_TYPE,
                MESSAGE_TYPE,
                MESSAGE_TYPE,
            ],
        )
        self.assertEqual(context.input[1]["call_id"], "call_1")

    def test_partial_parallel_tool_results_are_completed(self) -> None:
        self.chat.add_items([_function_call("call_1"), _function_call("call_2")])
        self.chat.add_item(_function_output("call_1", "first result"))

        context = self.chat.add_item(_user_message("Hello...?"))
        self.assertEqual(
            _item_types(context),
            [
                FUNCTION_CALL_TYPE,
                FUNCTION_CALL_TYPE,
                FUNCTION_CALL_OUTPUT_TYPE,
                FUNCTION_CALL_OUTPUT_TYPE,
                MESSAGE_TYPE,
            ],
        )
        self.assertEqual(context.input[2]["call_id"], "call_1")
        self.assertEqual(context.input[3]["call_id"], "call_2")
        self.assertEqual(context.input[3]["output"], INCOMPLETE_TOOL_RESULT)

    def test_leading_orphaned_tool_results_are_removed(self) -> None:
        short_chat = ChatManager("You are a test assistant.", max_messages=2)
        short_chat.add_item(_function_call("call_1"))
        short_chat.add_item(_function_output("call_1"))
        short_chat.add_item(_user_message("next"))

        remaining = list(short_chat._chat_history.messages["default"])
        self.assertEqual([item.type for item in remaining], [MESSAGE_TYPE])

    def test_user_name_is_prefixed_in_api_input_but_not_the_local_transcript(self) -> None:
        self.chat.add_user_message("Where is Alaska?", name="Steve")
        self.chat.add_item(_assistant_message("In the far north."))

        context = self.chat._build_context("default", add_date_time=False)
        self.assertEqual(context.input[0]["content"], "Steve: Where is Alaska?")
        self.assertEqual(
            self.chat.get_chat(),
            "Steve: Where is Alaska?\nBotto: In the far north.",
        )

    def test_request_uses_instructions_and_disables_storage(self) -> None:
        self.chat.add_user_message("Hello", name="Steve")
        request = self.chat.build_request(
            None,
            chat_id="default",
            add_date_time=False,
            allow_tool_calls=True,
        )

        self.assertEqual(request["instructions"], "You are a test assistant.")
        self.assertFalse(request["store"])
        self.assertEqual(request["include"], ["reasoning.encrypted_content"])
        self.assertNotIn("tools", request)
        self.assertNotIn("previous_response_id", request)

    def test_broken_completions_history_is_converted_and_repaired_on_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir)
            (storage_path / CHAT_HISTORY_FILE).write_text(
                json.dumps(
                    {
                        "messages": {
                            "-417681459": [
                                {
                                    "role": "user",
                                    "content": "A top safety researcher at Anthropic has warned AI...",
                                    "name": "Stephen",
                                },
                                {
                                    "role": "assistant",
                                    "name": "Botto",
                                    "tool_calls": [
                                        {
                                            "id": "call_Yj6AZxSRdNNmju6S1r8Ja7Xy",
                                            "type": "function",
                                            "function": {
                                                "name": "internet_search",
                                                "arguments": '{"query": "test"}',
                                            },
                                        }
                                    ],
                                },
                                {
                                    "role": "user",
                                    "content": "Hello...?",
                                    "name": "Stephen",
                                },
                            ]
                        }
                    },
                    indent=2,
                )
            )

            ChatManager("You are a test assistant.", storage_path=storage_path)

            saved = json.loads((storage_path / CHAT_HISTORY_FILE).read_text())
            messages = saved["messages"]["-417681459"]
            self.assertEqual(
                [message["type"] for message in messages],
                [
                    MESSAGE_TYPE,
                    FUNCTION_CALL_TYPE,
                    FUNCTION_CALL_OUTPUT_TYPE,
                    MESSAGE_TYPE,
                ],
            )
            self.assertEqual(
                messages[2]["call_id"],
                "call_Yj6AZxSRdNNmju6S1r8Ja7Xy",
            )
            self.assertEqual(messages[2]["output"], INCOMPLETE_TOOL_RESULT)


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from unittest.mock import patch

from simple_openai import SimpleOpenai
from simple_openai.constants import FULL_RESPONSES_URL
from simple_openai.models import open_ai_models


class DummyResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self.status_code = status_code
        self.text = json.dumps(payload)


def _message_payload(text: str) -> dict[str, object]:
    return {
        "id": "resp_text",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ],
    }


def _function_call_payload(call_id: str, name: str) -> dict[str, object]:
    return {
        "id": "resp_call",
        "output": [
            {
                "type": "reasoning",
                "id": "rs_1",
                "encrypted_content": "encrypted",
            },
            {
                "type": "function_call",
                "call_id": call_id,
                "name": name,
                "arguments": "{}",
            },
        ],
    }


class SimpleOpenaiResponsesTests(unittest.TestCase):
    def test_chat_request_uses_responses_endpoint_without_storage(self) -> None:
        client = SimpleOpenai("test-key", "You are a test assistant.")

        with patch(
            "simple_openai.simple_openai.requests.post",
            return_value=DummyResponse(_message_payload("Hi there")),
        ) as post:
            result = client.get_chat_response("Hello", name="Steve")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Hi there")
        post.assert_called_once()
        url = post.call_args.args[0]
        body = post.call_args.kwargs["json"]
        self.assertEqual(url, FULL_RESPONSES_URL)
        self.assertFalse(body["store"])
        self.assertEqual(body["reasoning"]["effort"], "none")
        self.assertNotIn("include", body)
        self.assertEqual(body["input"][0]["content"], "Steve: Hello")
        self.assertNotIn("previous_response_id", body)

    def test_function_call_loop_replays_local_items(self) -> None:
        client = SimpleOpenai("test-key", "You are a test assistant.")
        client.add_tool(
            open_ai_models.OpenAITool(
                function=open_ai_models.OpenAIFunction(
                    name="internet_search",
                    description="Search the internet",
                    parameters=open_ai_models.OpenAIParameters(properties={}),
                )
            ),
            lambda **kwargs: "search results",
        )

        with patch(
            "simple_openai.simple_openai.requests.post",
            side_effect=[
                DummyResponse(_function_call_payload("call_1", "internet_search")),
                DummyResponse(_message_payload("Here you go")),
            ],
        ) as post:
            result = client.get_chat_response("Find that", name="Steve")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Here you go")
        self.assertEqual(post.call_count, 2)

        second_body = post.call_args_list[1].kwargs["json"]
        item_types = [item["type"] for item in second_body["input"]]
        self.assertEqual(
            item_types,
            ["message", "function_call", "function_call_output"],
        )
        self.assertEqual(second_body["input"][2]["output"], "search results")
        self.assertEqual(second_body["tool_choice"], "none")
        self.assertEqual(second_body["reasoning"]["effort"], "none")
        self.assertFalse(second_body["store"])


if __name__ == "__main__":
    unittest.main()

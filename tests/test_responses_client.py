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


def _usage(
    input_tokens: int = 75,
    cached_tokens: int = 0,
    output_tokens: int = 1186,
    reasoning_tokens: int = 1024,
) -> dict[str, object]:
    return {
        "input_tokens": input_tokens,
        "input_tokens_details": {"cached_tokens": cached_tokens},
        "output_tokens": output_tokens,
        "output_tokens_details": {"reasoning_tokens": reasoning_tokens},
        "total_tokens": input_tokens + output_tokens,
    }


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
        "usage": _usage(),
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
        "usage": _usage(output_tokens=50, reasoning_tokens=40),
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
        self.assertEqual(body["reasoning"]["effort"], "low")
        self.assertEqual(body["max_output_tokens"], 4096)
        self.assertEqual(body["model"], "gpt-5.6-sol")
        self.assertNotIn("include", body)
        self.assertEqual(body["input"][0]["content"], "Steve: Hello")
        self.assertNotIn("previous_response_id", body)
        self.assertNotIn("prompt_cache_key", body)

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
        self.assertEqual(second_body["reasoning"]["effort"], "low")
        self.assertEqual(second_body["max_output_tokens"], 4096)
        self.assertFalse(second_body["store"])

    def test_client_model_is_sent_and_per_call_overrides_it(self) -> None:
        client = SimpleOpenai(
            "test-key", "You are a test assistant.", model="gpt-5.6-terra"
        )

        with patch(
            "simple_openai.simple_openai.requests.post",
            return_value=DummyResponse(_message_payload("Hi")),
        ) as post:
            client.get_chat_response("Hello", name="Steve")
            client.get_chat_response("Hello again", name="Steve", model="gpt-5.6-luna")

        self.assertEqual(post.call_args_list[0].kwargs["json"]["model"], "gpt-5.6-terra")
        self.assertEqual(post.call_args_list[1].kwargs["json"]["model"], "gpt-5.6-luna")

    def test_usage_is_logged_without_changing_the_public_response(self) -> None:
        client = SimpleOpenai("test-key", "You are a test assistant.")

        with patch(
            "simple_openai.simple_openai.requests.post",
            return_value=DummyResponse(_message_payload("Hi there")),
        ):
            with self.assertLogs("simple_openai.usage", level="INFO") as logs:
                result = client.get_chat_response("Hello", name="Steve")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Hi there")
        self.assertEqual(result.__dataclass_fields__.keys(), {"success", "message"})
        self.assertTrue(
            any("estimated cost" in message for message in logs.output)
        )
        self.assertTrue(any("chat_id" in message for message in logs.output))
        self.assertTrue(any("default" in message for message in logs.output))

    def test_tool_loop_logs_usage_for_each_http_call(self) -> None:
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
        ):
            with self.assertLogs("simple_openai.usage", level="INFO") as logs:
                client.get_chat_response("Find that", name="Steve")

        usage_logs = [message for message in logs.output if "OpenAI usage" in message]
        self.assertEqual(len(usage_logs), 2)


if __name__ == "__main__":
    unittest.main()

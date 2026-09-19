import unittest

from simple_openai.models import open_ai_models


class OpenAISchemaModelTests(unittest.TestCase):
    def test_nested_schema_fields_are_serialised(self) -> None:
        function = open_ai_models.OpenAIFunction(
            name="query_football_history",
            description="Query historical football data from the Football History API.",
            parameters=open_ai_models.OpenAIParameters(
                properties={
                    "request": open_ai_models.OpenAIParameter(
                        type="object",
                        properties={
                            "action": open_ai_models.OpenAIParameter(
                                type="string",
                                enum=[
                                    "get_aggregate_stats",
                                    "get_head_to_head",
                                ],
                            ),
                            "filters": open_ai_models.OpenAIParameter(
                                type="object",
                                additionalProperties=False,
                            ),
                        },
                        required=["action", "filters"],
                        additionalProperties=False,
                    )
                },
                required=["request"],
                additionalProperties=False,
            ),
        )

        payload = open_ai_models.OpenAITool(function=function).model_dump(
            exclude_none=True
        )

        request_schema = payload["function"]["parameters"]["properties"]["request"]
        self.assertEqual(
            request_schema["properties"]["action"]["enum"],
            ["get_aggregate_stats", "get_head_to_head"],
        )
        self.assertFalse(request_schema["additionalProperties"])
        self.assertFalse(payload["function"]["parameters"]["additionalProperties"])

    def test_responses_tool_is_internally_tagged_and_not_strict(self) -> None:
        tool = open_ai_models.ResponsesFunctionTool.from_openai_tool(
            open_ai_models.OpenAITool(
                function=open_ai_models.OpenAIFunction(
                    name="get_weather",
                    description="Look up the weather",
                    parameters=open_ai_models.OpenAIParameters(properties={}),
                )
            )
        )

        payload = tool.model_dump(exclude_none=True)
        self.assertEqual(payload["type"], "function")
        self.assertEqual(payload["name"], "get_weather")
        self.assertFalse(payload["strict"])
        self.assertNotIn("function", payload)

    def test_output_text_joins_message_items(self) -> None:
        result = open_ai_models.ResponsesResult.model_validate(
            {
                "id": "resp_123",
                "output": [
                    {"type": "reasoning", "id": "rs_1", "encrypted_content": "abc"},
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "Hello "},
                            {"type": "output_text", "text": "world"},
                        ],
                    },
                ],
            }
        )

        self.assertEqual(result.output_text(), "Hello world")
        self.assertTrue(result.output[0].is_reasoning())
        self.assertEqual(result.function_calls(), [])


if __name__ == "__main__":
    unittest.main()

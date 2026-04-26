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


if __name__ == "__main__":
    unittest.main()

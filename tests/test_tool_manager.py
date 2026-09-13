import unittest

from simple_openai.models import open_ai_models
from simple_openai.tool_manager import ToolManager


def _tool(name: str) -> open_ai_models.OpenAITool:
    return open_ai_models.OpenAITool(
        function=open_ai_models.OpenAIFunction(
            name=name,
            description="A test tool",
            parameters=open_ai_models.OpenAIParameters(properties={}),
        )
    )


class ToolManagerFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ToolManager()

    def test_function_exception_is_returned_as_a_string(self) -> None:
        def boom() -> str:
            raise RuntimeError("search timed out")

        self.manager.add_tool(_tool("internet_search"), boom)

        result = self.manager.call_function("internet_search")
        self.assertEqual(result, "Tool internet_search failed: search timed out")

    def test_invalid_arguments_are_returned_as_a_string(self) -> None:
        self.manager.add_tool(_tool("internet_search"), lambda **kwargs: "ok")

        result = self.manager.call_function_from_arguments(
            "internet_search", "not-json"
        )
        self.assertTrue(result.startswith("Tool internet_search failed:"))

    def test_non_object_arguments_are_returned_as_a_string(self) -> None:
        self.manager.add_tool(_tool("internet_search"), lambda **kwargs: "ok")

        result = self.manager.call_function_from_arguments("internet_search", "[1, 2]")
        self.assertEqual(
            result, "Tool internet_search failed: Tool arguments must be a JSON object"
        )

    def test_missing_function_still_returns_a_string(self) -> None:
        result = self.manager.call_function("no_such_tool")
        self.assertIn("does not exist", result)


if __name__ == "__main__":
    unittest.main()

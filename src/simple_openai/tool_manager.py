"""This module contains the tool manager.

The tool manager is used to manage the tools that can be called by the bot.

Define a function using the [OpenAITool](public_models.md/#src.simple_openai.models.open_ai_models.OpenAITool) model from models.py and add it to the tool manager using the add_tool method.

The tool should return a string.

The tool can optionally take keyword arguments, the keyword arguments should be defined in the OpenAITool model.

Call the tool using the call_function method for synchronous functions or the async_call_function method for asynchronous.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias

from .models import open_ai_models

ToolCallback: TypeAlias = Callable[..., str] | Callable[..., Awaitable[str]]


@dataclass
class OpenAIToolMapping:
    """OpenAI tool mapping

    This class represents an OpenAI tool mapping.

        Args:
            tool_definition (OpenAITool): The description of the tool
            function (ToolCallback): The function to call
    """

    tool_definition: open_ai_models.OpenAITool
    function: ToolCallback


class ToolManager:
    """Tool manager

    This class manages the tools that can be called by the bot.
    """

    def __init__(self) -> None:
        self._tools: dict[str, OpenAIToolMapping] = {}

    def add_tool(
        self, tool_definition: open_ai_models.OpenAITool, function: ToolCallback
    ) -> None:
        """Add a tool to the tool manager

        Args:
            tool_definition (OpenAITool): The tool definition
            function (ToolCallback): The function to call
        """
        # Add the function to the function manager
        self._tools[tool_definition.function.name] = OpenAIToolMapping(
            tool_definition, function
        )

    def get_json_tool_list(self) -> list[open_ai_models.ResponsesFunctionTool] | None:
        """Get the list of tools in Responses API format

        Returns:
            list[open_ai_models.ResponsesFunctionTool] | None: The list of tools or None if there are no tools
        """
        tools = [
            open_ai_models.ResponsesFunctionTool.from_openai_tool(tool.tool_definition)
            for tool in self._tools.values()
        ]

        if tools:
            return tools
        return None

    def _parse_arguments(self, arguments: str) -> dict[str, open_ai_models.JsonValue]:
        """Parse a tool-call arguments JSON object

        Args:
            arguments (str): The JSON arguments string from OpenAI

        Returns:
            dict[str, JsonValue]: The parsed arguments

        Raises:
            ValueError: If the arguments are not a JSON object
        """
        return open_ai_models.as_json_object(json.loads(arguments))

    def call_function(self, function_name: str, **kwargs: open_ai_models.JsonValue) -> str:
        """Call a function

        Args:
            function_name (str): The name of the function to call
            **kwargs: The keyword arguments to pass to the function

        Returns:
            str: The result of the function
        """
        # Check that the function exists
        if function_name not in self._tools:
            # Return text to tell the bot it hallucinated the function
            return f"Tool {function_name} does not exist, please answer the last question again."

        try:
            result = self._tools[function_name].function(**kwargs)
        except Exception as exc:
            return f"Tool {function_name} failed: {exc}"

        if isinstance(result, str):
            return result
        return f"Tool {function_name} failed: expected a string result"

    def call_function_from_arguments(
        self, function_name: str, arguments: str
    ) -> str:
        """Call a function from an OpenAI tool-call arguments string

        Invalid JSON and function errors are returned as a string so a tool
        result can still be written to the chat history.

        Args:
            function_name (str): The name of the function to call
            arguments (str): The JSON arguments string from OpenAI

        Returns:
            str: The result of the function
        """
        try:
            parsed_arguments = self._parse_arguments(arguments)
        except Exception as exc:
            return f"Tool {function_name} failed: {exc}"

        return self.call_function(function_name, **parsed_arguments)

    async def async_call_function(
        self, function_name: str, **kwargs: open_ai_models.JsonValue
    ) -> str:
        """Call a function

        Args:
            function_name (str): The name of the function to call
            **kwargs: The keyword arguments to pass to the function

        Returns:
            str: The result of the function
        """
        # Check that the function exists
        if function_name not in self._tools:
            # Return text to tell the bot it hallucinated the function
            return f"Function {function_name} does not exist, please answer the last question again."

        try:
            result = self._tools[function_name].function(**kwargs)
            if isinstance(result, str):
                return result
            return await result
        except Exception as exc:
            return f"Tool {function_name} failed: {exc}"

    async def async_call_function_from_arguments(
        self, function_name: str, arguments: str
    ) -> str:
        """Call a function from an OpenAI tool-call arguments string

        Invalid JSON and function errors are returned as a string so a tool
        result can still be written to the chat history.

        Args:
            function_name (str): The name of the function to call
            arguments (str): The JSON arguments string from OpenAI

        Returns:
            str: The result of the function
        """
        try:
            parsed_arguments = self._parse_arguments(arguments)
        except Exception as exc:
            return f"Tool {function_name} failed: {exc}"

        return await self.async_call_function(function_name, **parsed_arguments)

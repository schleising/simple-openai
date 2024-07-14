"""This module contains the tool manager.

The tool manager is used to manage the toold that can be called by the bot.

Define a function using the [OpenAITool](public_models.md/#src.simple_openai.models.open_ai_models.OpenAITool) model from models.py and add it to the tool manager using the add_tool method.

The tool should return a string.

The tool can optionally take keyword arguments, the keyword arguments should be defined in the OpenAITool model.

Call the tool using the call_function method for synchronous functions or the async_call_function method for asynchronous.
"""

from typing import Any, Callable
from dataclasses import dataclass

from .models import open_ai_models


@dataclass
class OpenAIToolMapping:
    """OpenAI tool mapping

    This class represents an OpenAI tool mapping.

    Args:
        tool_definition (OpenAITool): The description of the tool
        function (Callable): The function to call
    """

    tool_definition: open_ai_models.OpenAITool
    function: Callable


class ToolManager:
    """Tool manager

    This class manages the tools that can be called by the bot.
    """

    def __init__(self) -> None:
        self._tools: dict[str, OpenAIToolMapping] = {}

    def add_tool(
        self, tool_definition: open_ai_models.OpenAITool, function: Callable
    ) -> None:
        """Add a tool to the tool manager

        Args:
            tool_definition (OpenAITool): The tool definition
            function (Callable): The function to call
        """
        # Add the function to the function manager
        self._tools[tool_definition.function.name] = OpenAIToolMapping(
            tool_definition, function
        )

    def get_json_tool_list(self) -> list[open_ai_models.OpenAITool] | None:
        """Get the list of tools

        Returns:
            list[open_ai_models.OpenAITool] | None: The list of tools or None if there are no tools
        """
        # Get the list of functions
        tools = [tool.tool_definition for tool in self._tools.values()]

        if tools:
            # Return the list of functions
            return tools
        else:
            # Return None
            return None

    def call_function(self, function_name: str, **kwargs: dict[str, Any]) -> str:
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
        else:
            # Call the function
            return self._tools[function_name].function(**kwargs)

    async def async_call_function(
        self, function_name: str, **kwargs: dict[str, Any]
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
        else:
            # Call the function
            return await self._tools[function_name].function(**kwargs)

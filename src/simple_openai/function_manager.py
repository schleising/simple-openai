"""This module contains the function manager.

The function manager is used to manage the functions that can be called by the bot.

Define a function using the [OpenAIFunction](public_models.md/#src.simple_openai.models.open_ai_models.OpenAIFunction) model from models.py and add it to the function manager using the add_function method.

The function should return a string.

The function can optionally take keyword arguments, the keyword arguments should be defined in the OpenAIFunction model.

Call the function using the call_function method for synchronous functions or the async_call_function method for asynchronous functions.
"""

from typing import Any, Callable
from dataclasses import dataclass

from .models import open_ai_models

@dataclass
class OpenAIFunctionMapping:
    """OpenAI function mapping

    This class represents an OpenAI function mapping.

    Args:
        function_definition (OpenAIFunction): The description of the function
        function (Callable): The function to call
    """
    function_definition: open_ai_models.OpenAIFunction
    function: Callable

class FunctionManager:
    """Function manager

    This class manages the functions that can be called by the bot.
    """
    
    def __init__(self) -> None:
        self._functions: dict[str, OpenAIFunctionMapping] = {}

    def add_function(self, function_definition: open_ai_models.OpenAIFunction, function: Callable) -> None:
        """Add a function to the function manager

        Args:
            function_definition (OpenAIFunction): The function definition
            function (Callable): The function to call
        """
        # Add the function to the function manager
        self._functions[function_definition.name] = OpenAIFunctionMapping(function_definition, function)

    def get_json_function_list(self) -> list[open_ai_models.OpenAIFunction] | None:
        """Get the list of functions

        Returns:
            list[open_ai_models.OpenAIFunction] | None: The list of functions or None if there are no functions
        """
        # Get the list of functions
        functions = [function.function_definition for function in self._functions.values()]

        if functions:
            # Return the list of functions
            return functions
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
        if function_name not in self._functions:
            # Return text to tell the bot it hallucinated the function
            return f'Function {function_name} does not exist, please answer the last question again.'
        else:
            # Call the function
            return self._functions[function_name].function(**kwargs)

    async def async_call_function(self, function_name: str, **kwargs: dict[str, Any]) -> str:
        """Call a function

        Args:
            function_name (str): The name of the function to call
            **kwargs: The keyword arguments to pass to the function

        Returns:
            str: The result of the function
        """
        # Check that the function exists
        if function_name not in self._functions:
            # Return text to tell the bot it hallucinated the function
            return f'Function {function_name} does not exist, please answer the last question again.'
        else:
            # Call the function
            return await self._functions[function_name].function(**kwargs)

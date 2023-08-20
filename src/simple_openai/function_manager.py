from typing import Callable
from dataclasses import dataclass

from .models import open_ai_models

@dataclass
class OpenAIFunctionMapping:
    """OpenAI function mapping

    This class represents an OpenAI function mapping.

    Args:
        function_definition (open_ai_models.OpenAIFunction): The description of the function
        function (Callable): The function to call
    """
    function_definition: open_ai_models.OpenAIFunction
    function: Callable

class FunctionManager:
    """Function manager

    This class manages the functions that can be called by the chat manager.
    """
    
    def __init__(self) -> None:
        self._functions: dict[str, OpenAIFunctionMapping] = {}

    def add_function(self, function_definition: open_ai_models.OpenAIFunction, function: Callable) -> None:
        """Add a function to the chat manager

        Args:
            function_definition (open_ai_models.OpenAIFunction): The function definition
            function (Callable): The function to call
        """
        # Add the function to the chat manager
        self._functions[function_definition.name] = OpenAIFunctionMapping(function_definition, function)

    def get_json_function_list(self) -> list[open_ai_models.OpenAIFunction] | None:
        """Get the list of functions as JSON

        Returns:
            list[str]: The list of functions as JSON
        """
        # Get the list of functions
        functions = [function.function_definition for function in self._functions.values()]

        if functions:
            # Return the list of functions
            return functions
        else:
            # Return None
            return None

    def call_function(self, function_name: str, **kwargs) -> str:
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

    async def async_call_function(self, function_name: str, **kwargs) -> str:
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

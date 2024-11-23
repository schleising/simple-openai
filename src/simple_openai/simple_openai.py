"""Simple OpenAI API wrapper

The is the synchronous version of the Simple OpenAI API wrapper which uses the [`requests`](https://requests.readthedocs.io/en/latest/) library.

If you wish to use the async version, you should use the [AsyncSimple OpenAI API wrapper](async_simple_openai.md) instead.
"""

import json
from pathlib import Path
from typing import Callable
import requests

from . import constants
from .models import open_ai_models
from .responses import SimpleOpenaiResponse
from . import chat_manager
from . import tool_manager


class SimpleOpenai:
    """Simple OpenAI API wrapper

    This class implements the Simple OpenAI API wrapper.

    To use this class, you need to have an OpenAI API key. You can get one from [Openai](https://platform.openai.com).

    An optional storage path can be provided.  If a storage path is provided, the chat messages will be stored in the directory specified by the storage path.  If no storage path is provided, the chat messages will not be stored.

    Args:
        api_key (str): Your OpenAI API key
        system_message (str): The system message to add to the start of the chat
        storage_path (Path, optional): The path to the storage directory. Defaults to None.
        timezone (str, optional): The timezone to use for the chat messages. Defaults to 'UTC'.

    !!!Example
        ```python
        from simple_openai import SimpleOpenai

        def main():
            # Create a system message
            system_message = "You are a helpful chatbot. You are very friendly and helpful. You are a good friend to have."

            # Create the client
            client = SimpleOpenai(api_key, system_message)

            # Create tasks for the chat response and the image response
            result = client.get_chat_response("Hello, how are you?", name="Bob", chat_id="Group 1")

            # Print the result
            if result.success:
                # Print the message
                print(f'Success: {result.message}')
            else:
                # Print the error
                print(f'Error: {result.message}')

            result = client.get_image_url("A cat")

            # Print the result
            if result.success:
                # Print the message
                print(f'Success: {result.message}')
            else:
                # Print the error
                print(f'Error: {result.message}')

        if __name__ == "__main__":
            # Run the main function
            main()
        ```
    """

    def __init__(
        self,
        api_key: str,
        system_message: str,
        storage_path: Path | None = None,
        timezone: str = "UTC",
    ) -> None:
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Create the chat manager
        self._chat = chat_manager.ChatManager(
            system_message, storage_path=storage_path, timezone=timezone
        )

        # Create the tool manager
        self._tool_manager = tool_manager.ToolManager()

    def update_system_message(self, system_message: str) -> None:
        """Update the system message

        Args:
            system_message (str): The new system message
        """
        self._chat.update_system_message(system_message)

    def add_tool(
        self, tool_definition: open_ai_models.OpenAITool, function: Callable
    ) -> None:
        """Add a tool to the tool manager

        Args:
            tool_definition (open_ai_models.OpenAITool): The tool definition
            function (Callable): The function to call
        """
        self._tool_manager.add_tool(tool_definition, function)

    def get_chat_response(
        self,
        prompt: str,
        name: str,
        chat_id: str = constants.DEFAULT_CHAT_ID,
        add_date_time: bool = False,
    ) -> SimpleOpenaiResponse:
        """Get a chat response from OpenAI

        An optional chat ID can be provided.  If a chat ID is provided, the chat will be continued from the chat with the specified ID.  If no chat ID is provided, all messages will be mixed into a single list.

        Args:
            prompt (str): The prompt to use for the chat response
            name (str): The name of the person talking to the bot
            chat_id (str, optional): The ID of the chat to continue. Defaults to DEFAULT_CHAT_ID.
            add_date_time (bool, optional): Whether to add the date and time to the start of the prompt. Defaults to False.

        Returns:
            SimpleOpenaiResponse: The chat response, the value of `success` should be checked before using the value of `message`
        """

        # Create the request body
        messages = self._chat.add_message(
            open_ai_models.ChatMessage(role="user", content=prompt, name=name),
            chat_id=chat_id,
            add_date_time=add_date_time,
        ).messages

        # Create the request body
        request_body = open_ai_models.ChatRequest(
            messages=messages,
            tools=self._tool_manager.get_json_tool_list(),
            tool_choice="auto",
        )

        # Delete the tools from the request body if there are no tool
        if request_body.tools is None:
            del request_body.tools
            del request_body.tool_choice

        # Send the request
        response1 = requests.post(
            constants.FULL_CHAT_URL,
            json=request_body.model_dump(),
            headers=self._headers,
        )

        # Check the status code
        if response1.status_code == requests.codes.OK:
            # Parse the response body
            response_body = open_ai_models.ChatResponse.model_validate_json(
                response1.text
            )

            # Check if a function was called
            if (
                response_body.choices[0].finish_reason == constants.OPEN_AI_TOOL_CALLS
                and response_body.choices[0].message.tool_calls is not None
            ):
                # Call the function
                new_prompt = self._tool_manager.call_function(
                    response_body.choices[0].message.tool_calls[0].function.name,
                    **json.loads(response_body.choices[0].message.tool_calls[0].function.arguments),
                )

                # Add the response to the chat
                self._chat.add_message(
                    open_ai_models.ChatMessage(
                        role="assistant",
                        content=response_body.choices[0]
                        .message.tool_calls[0]
                        .function.model_dump_json(),
                        name="Botto",
                    ),
                    chat_id=chat_id,
                    add_date_time=add_date_time,
                )

                # Add the message to the chat
                messages = self._chat.add_message(
                    open_ai_models.ChatMessage(
                        role="function", content=new_prompt, name="Botto"
                    ),
                    chat_id=chat_id,
                    add_date_time=add_date_time,
                ).messages

                # Create the request body
                request_body = open_ai_models.ChatRequest(
                    messages=messages,
                    tools=self._tool_manager.get_json_tool_list(),
                    tool_choice="none",
                )

                # Send the request
                response2 = requests.post(
                    constants.FULL_CHAT_URL,
                    json=request_body.model_dump(),
                    headers=self._headers,
                )

                # Check the status code
                if response2.status_code == requests.codes.OK:
                    # Parse the response body
                    response_body = open_ai_models.ChatResponse.model_validate_json(
                        response2.text
                    )

                    # Create the response
                    if response_body.choices[0].message.content is not None:
                        open_ai_response = SimpleOpenaiResponse(
                            True, response_body.choices[0].message.content
                        )
                    else:
                        open_ai_response = SimpleOpenaiResponse(True, "No response")

                    # Add the response to the chat
                    self._chat.add_message(
                        open_ai_models.ChatMessage(
                            role="assistant",
                            content=open_ai_response.message,
                            name="Botto",
                        ),
                        chat_id=chat_id,
                        add_date_time=add_date_time,
                    )
                else:
                    # Parse the error response body
                    response_body = open_ai_models.ErrorResponse.model_validate_json(
                        response2.text
                    )

                    # Create the response
                    open_ai_response = SimpleOpenaiResponse(
                        False, response_body.error.message
                    )
            else:
                # Create the response
                if response_body.choices[0].message.content is not None:
                    open_ai_response = SimpleOpenaiResponse(
                        True, response_body.choices[0].message.content
                    )
                else:
                    open_ai_response = SimpleOpenaiResponse(True, "No response")

                # Add the response to the chat
                self._chat.add_message(
                    open_ai_models.ChatMessage(
                        role="assistant", content=open_ai_response.message, name="Botto"
                    ),
                    chat_id=chat_id,
                    add_date_time=add_date_time,
                )
        else:
            # Parse the error response body
            response_body = open_ai_models.ErrorResponse.model_validate_json(
                response1.text
            )

            # Create the response
            open_ai_response = SimpleOpenaiResponse(False, response_body.error.message)

        # Return the response
        return open_ai_response

    def get_image_url(self, prompt: str, style: str = "vivid") -> SimpleOpenaiResponse:
        """Get an image response from OpenAI

        Args:
            prompt (str): The prompt to use
            style (str, optional): The style of the image. Defaults to 'vivid'.

        Returns:
            SimpleOpenaiResponse: The image response, the value of `success` should be checked before using the value of `message`
        """

        # Create the request body
        request_body = open_ai_models.ImageRequest(prompt=prompt, style=style)

        # Send the request
        response = requests.post(
            constants.FULL_IMAGE_URL,
            json=request_body.model_dump(),
            headers=self._headers,
        )

        # Check the status code
        if response.status_code == requests.codes.OK:
            # Parse the response body
            response_body = open_ai_models.ImageResponse.model_validate_json(
                response.text
            )

            # Create the response
            response = SimpleOpenaiResponse(True, response_body.data[0].url)
        else:
            # Parse the error response body
            response_body = open_ai_models.ErrorResponse.model_validate_json(
                response.text
            )

            # Create the response
            response = SimpleOpenaiResponse(False, response_body.error.message)

        # Return the response
        return response

    def get_chat_history(self, chat_id: str) -> str:
        """Get the chat history

        Args:
            chat_id (str): The ID of the chat

        Returns:
            str: The chat history
        """
        # Get the chat history
        chat_history = self._chat.get_chat(chat_id)

        # Return the chat history
        return chat_history

    def get_truncated_chat_history(self, chat_id: str) -> str:
        """Get the truncated chat history, limited to the last 4,000 characters

        Args:
            chat_id (str): The ID of the chat

        Returns:
            str: The truncated chat history
        """
        # Get the chat history
        chat_history = self._chat.get_truncated_chat(chat_id)

        # Return the chat history
        return chat_history

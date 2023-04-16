"""Async Simple OpenAI API wrapper

The is the async version of the Simple OpenAI API wrapper which uses the [`aiohttp`](https://docs.aiohttp.org/en/stable/index.html) library.

It is intended for use with asyncio applications.  If you are not using asyncio, you should use the [Simple OpenAI API wrapper](/simple_openai/simple_openai/) instead.
"""

import aiohttp

from . import constants
from .models import open_ai_models

from .responses import SimpleOpenaiResponse

class AsyncSimpleOpenai:
    """Async Simple OpenAI API wrapper

    This class implements the Async Simple OpenAI API wrapper.

    To use this class, you need to have an OpenAI API key. You can get one from [Openai](https://platform.openai.com).

    Args:
        api_key (str): Your OpenAI API key

    !!!Example
        ```python
        from simple_openai import AsyncSimpleOpenai
        import asyncio

        async def main():
            # Create the client
            client = AsyncSimpleOpenai(api_key)

            # Create tasks for the chat response and the image response
            tasks = [
                client.get_chat_response("Hello, how are you?"),
                client.get_image_url("A cat"),
            ]

            # Wait for the tasks to complete
            for task in asyncio.as_completed(tasks):
                # Get the result
                result = await task

                # Print the result
                if result.success:
                    # Print the message
                    print(f'Success: {result.message}')
                else:
                    # Print the error
                    print(f'Error: {result.message}')

        if __name__ == "__main__":
            # Run the main function
            asyncio.run(main())
        ```
    """
    def __init__(self, api_key: str) -> None:
        self._headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

    async def get_chat_response(self, prompt: str) -> SimpleOpenaiResponse:
        """Get a chat response from OpenAI

        Args:
            prompt (str): The prompt to use for the chat response

        Returns:
            SimpleOpenaiResponse: The chat response, the value of `success` should be checked before using the value of `message`

        !!!Example
            ```python
            from simple_openai import AsyncSimpleOpenai
            import asyncio

            async def main():
            
                # Create the client
                client = AsyncSimpleOpenai(api_key)

                # Get the chat response
                response = await client.get_chat_response("Hello, how are you?")

                # Check if the request was successful
                if response.success:
                    # Print the chat response
                    print(f'Chat response: {response.message}')
                else:
                    # Print the error message
                    print(f'Error: {response.message}')

            if __name__ == "__main__":
                asyncio.run(main())
            ```

        """

        # Create the request body
        chat_message = open_ai_models.ChatMessage(content=prompt)
        request_body = open_ai_models.ChatRequest(messages=[chat_message])

        # Open a session
        async with aiohttp.ClientSession(headers=self._headers, base_url=constants.BASE_URL) as session:
            # Send the request
            async with session.post(constants.CHAT_URL, json=request_body.dict()) as response:
                # Check the status code
                if response.status == 200:
                    # Parse the response body
                    response_body = open_ai_models.ChatResponse.parse_raw(await response.text())

                    # Create the response
                    response = SimpleOpenaiResponse(True, response_body.choices[0].message.content)
                else:
                    # Parse the error response body
                    response_body = open_ai_models.ErrorResponse.parse_raw(await response.text())

                    # Create the response
                    response = SimpleOpenaiResponse(False, response_body.error.message)

                # Return the response
                return response

    async def get_image_url(self, prompt: str) -> SimpleOpenaiResponse:
        """Get an image response from OpenAI

        Args:
            prompt (str): The prompt to use

        Returns:
            SimpleOpenaiResponse: The image response, the value of `success` should be checked before using the value of `message`

        !!!Example
            ```python
            from simple_openai import AsyncSimpleOpenai
            import asyncio

            async def main():
            
                # Create the client
                client = AsyncSimpleOpenai(api_key)

                # Get the image response
                response = await client.get_image_url("A cat")

                # Check if the request was successful
                if response.success:
                    # Print the image URL
                    print(f'Image Generated Successfully, it can be found at {response.message}')
                else:
                    # Print the error message
                    print(f'Image Generation Failed, Error: {response.message}')

            if __name__ == "__main__":
                asyncio.run(main())
            ```
        """
            
        # Create the request body
        request_body = open_ai_models.ImageRequest(prompt=prompt)

        # Open a session
        async with aiohttp.ClientSession(headers=self._headers, base_url=constants.BASE_URL) as session:
            # Send the request
            async with session.post(constants.IMAGE_URL, json=request_body.dict()) as response:
                # Check the status code
                if response.status == 200:
                    # Parse the response body
                    response_body = open_ai_models.ImageResponse.parse_raw(await response.text())

                    # Create the response
                    response = SimpleOpenaiResponse(True, response_body.data[0].url)
                else:
                    # Parse the error response body
                    response_body = open_ai_models.ErrorResponse.parse_raw(await response.text())

                    # Create the response
                    response = SimpleOpenaiResponse(False, response_body.error.message)

                # Return the response
                return response

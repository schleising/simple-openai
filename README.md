# simple-openai

This is a simple wrapper around the OpenAI API.  It's not meant to be a full-featured library, but rather a simple way to get started with the API.

The library provides both synchronous and asynchronous methods for interacting with the API.

## Installation

Install using pip:

```bash
pip install simple-openai
```

## Usage

### Calling the API

For the synchronous version, you can use the following code:

    from simple_openai import SimpleOpenai

    def main():
        # Initialise a storage location
        storage_location = Path("/path/to/storage")

        # Create a system message
        system_message = "You are a helpful chatbot. You are very friendly and helpful. You are a good friend to have."

        # Create the client
        client = SimpleOpenai(api_key, system_message, storage_location)

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

For the asynchronous version, you can use the following code:

    from simple_openai import AsyncSimpleOpenai
    import asyncio

    async def main():
        # Initialise a storage location
        storage_location = Path("/path/to/storage")

        # Create a system message
        system_message = "You are a helpful chatbot. You are very friendly and helpful. You are a good friend to have."

        # Create the client
        client = AsyncSimpleOpenai(api_key, system_message, storage_location)

        # Create tasks for the chat response and the image response
        tasks = [
            client.get_chat_response("Hello, how are you?", name="Bob", chat_id="Group 1"),
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

### Output

The output of the functions is a [SimpleOpenaiResponse](https://schleising.github.io/simple-openai/simple_openai/responses/#src.simple_openai.responses.SimpleOpenaiResponse) object, which contains the following properties:

- `success` - A boolean indicating whether the request was successful or not.
- `message` - The message returned by the API.

### Functions

Functions can be added to the client using the `add_function` method. This method takes a function name and a function as arguments. The function should take an [OpenAIFunction](https://schleising.github.io/simple-openai/simple_openai/public_models/#src.simple_openai.models.open_ai_models.OpenAIFunction) object as its first argument, and the Python function itself as the second argument.

The Python function should return a string, which will be passed to the API using the `function` role

## Documentation

The documentation is available on [GitHub](https://schleising.github.io/simple-openai/)
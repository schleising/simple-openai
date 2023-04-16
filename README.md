# simple-openai

This is a simple wrapper around the OpenAI API.  It's not meant to be a full-featured library, but rather a simple way to get started with the API.

The library provides both synchronous and asynchronous methods for interacting with the API.

## Installation

```bash
pip install simple-openai
```

## Usage

### Calling the API

For the synchronous version, you can use the following code:

    from simple_openai import SimpleOpenai

    def main():
        # Create the client
        client = SimpleOpenai(api_key)

        # Create tasks for the chat response and the image response
        result = client.get_chat_response("Hello, how are you?")

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

### Output

The output of the functions is a [SimpleOpenaiResponse](https://schleising.github.io/simple-openai/simple_openai/responses/#src.simple_openai.responses.SimpleOpenaiResponse) object, which contains the following properties:

- `success` - A boolean indicating whether the request was successful or not.
- `message` - The message returned by the API.

## Documentation

The documentation is available on [GitHub](https://schleising.github.io/simple-openai/)
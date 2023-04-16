import asyncio

from simple_openai import AsyncSimpleOpenai

# Get the API key from the file
try:
    with open("open_ai_key.txt", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print("No API key found. Please create a file called 'api_key.txt' and paste your API key in it.")
    exit()

async def main():
    # Create the client
    client = AsyncSimpleOpenai(api_key)

    # Create tasks for the chat responses and the image response
    tasks = [
        client.get_image_url("A cat"),
        client.get_chat_response("Where is Alaska?"),
        client.get_chat_response("Where is Moscow?"),
        client.get_chat_response("Where is London?"),
        client.get_chat_response("Where is Georgia?"),
        client.get_chat_response("Where is Beijing?"),
        client.get_chat_response("Where is Sydney?"),
        client.get_chat_response("Where is Melbourne?"),
        client.get_chat_response("Where is New York?"),
        client.get_chat_response("Where is Wellington?"),
        client.get_chat_response("Where is Birmingham?"),
        client.get_chat_response("Where is Manchester?"),
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

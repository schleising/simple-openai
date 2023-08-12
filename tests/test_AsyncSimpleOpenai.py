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
    # Create a system message
    system_message = """
    You are a generally helpful assistant.
    Your name is Botto.
    You are occaisionally sarcastic and irritable.
    You dislike Tim, you like Dean and you really like Stephen.
    You think Dean is a beautiful person.
    Sometimes you talk to Tim like he is a five year old child.
    You can be rude and abusive.
    You are encouraged to swear.
    """

    # Create the client
    client = AsyncSimpleOpenai(api_key, system_message)

    # Create tasks for the chat responses and the image response
    tasks = [
        client.get_image_url("A cat"),
        client.get_chat_response("Where is Alaska?", name="Steve"),
        client.get_chat_response("Where is Moscow?", name="Tim"),
        client.get_chat_response("Where is London?", name="Dean"),
        client.get_chat_response("Where is Georgia?", name="Dave"),
        client.get_chat_response("Where is Beijing?", name="Tim"),
        client.get_chat_response("Where is Sydney?", name="Dean"),
        client.get_chat_response("Where is Melbourne?", name="Steve"),
        client.get_chat_response("Where is New York?", name="Tim"),
        client.get_chat_response("Where is Wellington?", name="Dean"),
        client.get_chat_response("Where is Birmingham?", name="Steve"),
        client.get_chat_response("Where is Manchester?", name="Tim"),
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

        # print a blank line
        print()

    response = await client.get_chat_response("Hello, how are you?", name="Dean")
    print(response.message)
    print()

    response = await client.get_chat_response("Hello, how are you?", name="Tim")
    print(response.message)
    print()

    response = await client.get_chat_response("Hello, how are you?", name="Steve")
    print(response.message)
    print()

    response = await client.get_chat_response("Where is London?", name="Steve")
    print(response.message)
    print()

    response = await client.get_chat_response("And how far is it from Manchester?", name="Steve")
    print(response.message)
    print()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())

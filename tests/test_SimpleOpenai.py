from simple_openai import SimpleOpenai

# Get the API key from the file
try:
    with open("open_ai_key.txt", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print("No API key found. Please create a file called 'api_key.txt' and paste your API key in it.")
    exit()

def main():
    # Create the client
    client = SimpleOpenai(api_key)

    # Create a list of results for the chat responses and the image response
    results = [
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

    # Get the results
    for result in results:
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

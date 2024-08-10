from pathlib import Path

import requests

from simple_openai import SimpleOpenai
from simple_openai.models import open_ai_models

FOOTBALL_API_MATCH_URL = "https://schleising.net/football/api"

# Get the API key from the file
try:
    with open("open_ai_key.txt", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print(
        "No API key found. Please create a file called 'api_key.txt' and paste your API key in it."
    )
    exit()


def initiate_chat():
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
    client = SimpleOpenai(
        api_key, system_message, Path("storage"), timezone="Europe/London"
    )

    # Create tasks for the chat responses and the image response
    results = [
        client.get_image_url("A cat"),
        client.get_chat_response("Where is Alaska?", name="Steve"),
        client.get_chat_response("Where is New York?", name="Tim"),
        client.get_chat_response("Where is Wellington?", name="Dean"),
        client.get_chat_response(
            "What day is it tomorrow?", name="Steve", add_date_time=True
        ),
        client.get_chat_response(
            "And what day of the week is that?", name="Steve", add_date_time=True
        ),
        client.get_chat_response("What time is it?", name="Steve", add_date_time=True),
    ]

    # Get the results
    for result in results:
        # Print the result
        if result.success:
            # Print the message
            print(f"Success: {result.message}")
        else:
            # Print the error
            print(f"Error: {result.message}")

        # print a blank line
        print()

    response = client.get_chat_response(
        "Where is London?", name="Steve", chat_id="Group 1"
    )
    print(response.message)
    print()

    response = client.get_chat_response(
        "Where is Moscow?", name="Tim", chat_id="Group 2"
    )
    print(response.message)
    print()

    response = client.get_chat_response(
        "And how far is it from Manchester?", name="Dean", chat_id="Group 1"
    )
    print(response.message)
    print()

    response = client.get_chat_response(
        "And how far is it from Manchester?", name="Dave", chat_id="Group 2"
    )
    print(response.message)
    print()


def load_and_summarise_chat():
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
    client = SimpleOpenai(api_key, system_message, Path("storage"))

    response = client.get_chat_response(
        "Summarise this conversation", name="Dean", chat_id="Group 1"
    )
    print(f"Group 1 Summary: {response.message}")
    print()

    response = client.get_chat_response(
        "Summarise this conversation", name="Tim", chat_id="Group 2"
    )
    print(f"Group 2 Summary: {response.message}")
    print()


def test_chat_history():
    # Create the client
    client = SimpleOpenai(api_key, "", Path("storage"))

    # Test the chat history
    chat = client.get_chat_history("Group 1")
    print("Group 1 Chat:")
    print(chat)
    print()

    chat = client.get_chat_history("Group 2")
    print("Group 2 Chat:")
    print(chat)


def test_functions():
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
    client = SimpleOpenai(
        api_key, system_message, Path("storage"), timezone="Europe/London"
    )

    func = open_ai_models.OpenAIFunction(
        name="football_scores_and_fixtures",
        description="Gets the football scores and fixtures for today's matches",
        parameters=open_ai_models.OpenAIParameters(
            properties={},
            required=[],
        ),
    )

    tool = open_ai_models.OpenAITool(function=func)

    def scores():
        """Returns the football scores for today's matches"""
        print("Getting Matches...")

        headers = {
            "Content-Type": "application/json",
        }

        # Send the request
        response = requests.get(FOOTBALL_API_MATCH_URL, headers=headers)

        # Check the status code
        if response.status_code == requests.codes.ok:
            # Get the response content
            content = response.text

            # Print success
            print("Got Matches")
        else:
            # Return an error
            content = f"Error: {response.status_code}"

            # Print the error
            print(content)

        return content

    # Add a tool
    client.add_tool(tool, scores)

    # Create a message to reuest football scores
    response = client.get_chat_response("Where is Canada?", name="Dean")

    # Print the response
    print(response.message)
    print()

    # Create a message to reuest football scores
    response = client.get_chat_response(
        "What are today's football scores?", name="Dean", add_date_time=True
    )

    # Print the response
    print(response.message)
    print()


def main():
    # Initialise the chat
    initiate_chat()

    # Load and summarise the chat
    load_and_summarise_chat()

    # Test functions
    test_functions()

    # Test chat history
    test_chat_history()


if __name__ == "__main__":
    # Run the main function
    main()

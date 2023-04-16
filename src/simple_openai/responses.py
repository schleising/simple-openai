from dataclasses import dataclass

@dataclass
class SimpleOpenaiResponse:
    """Simple OpenAI API response

    This class represents a response from the Simple OpenAI API.

    The value of `success` should be checked before using the value of `message`.

    If `success` is True,

    - For a chat response, `message` will contain the chat response.
    - For an image response, `message` will contain the image URL.

    If `success` is False, `message` will contain the error message.

    Args:
        success (bool): True if the request was successful, False otherwise
        message (str): The message of the response
    """
    success: bool
    message: str

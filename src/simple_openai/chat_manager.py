"""Chat manager for the simple openai app

This module contains the chat manager for the simple openai app.

The chat manager is used to manage the chat messages and create the chat, it limits the number of messages in the chat to 11 by default and adds the system message to the start of the list.
"""


from collections import deque

from .models import open_ai_models

class ChatManager:
    def __init__(self, system_message: str, max_messages = 11) -> None:
        """Initialise the chat manager

        Args:
            system_message (str): The system message to add to the start of the chat
            max_messages (int, optional): The maximum number of messages in the chat. Defaults to 11.
        """
        self._system_message = system_message

        # initialise a deque of messages not including the system message
        self._messages: deque[open_ai_models.ChatMessage] = deque(maxlen=max_messages)

    def add_message(self, message: open_ai_models.ChatMessage) -> open_ai_models.Chat:
        """Add a message to the chat

        Args:
            message (open_ai_models.ChatMessage): The message to add to the chat

        Returns:
            open_ai_models.Chat: The chat
        """
        # Add the message to the deque
        self._messages.append(message)

        # Create the chat adding the system message to the start
        chat = open_ai_models.Chat(messages=[
            open_ai_models.ChatMessage(role='system', content=self._system_message, name='System')
        ] + list(self._messages))

        # Return the chat
        return chat

from pathlib import Path


BASE_URL = "https://api.openai.com"
CHAT_URL = "/v1/chat/completions"
IMAGE_URL = "/v1/images/generations"

FULL_CHAT_URL = BASE_URL + CHAT_URL
FULL_IMAGE_URL = BASE_URL + IMAGE_URL

MAX_CHAT_HISTORY = 21
CHAT_HISTORY_FILE = Path("chat_history.pickle")
DEFAULT_CHAT_ID = "default"

OPEN_AI_TOOL_CALLS = "tool_calls"

from pathlib import Path


BASE_URL = "https://api.openai.com"
RESPONSES_URL = "/v1/responses"
IMAGE_URL = "/v1/images/generations"

FULL_RESPONSES_URL = BASE_URL + RESPONSES_URL
FULL_IMAGE_URL = BASE_URL + IMAGE_URL

MAX_CHAT_HISTORY = 21
CHAT_HISTORY_FILE = Path("chat_history.json")
DEFAULT_CHAT_ID = "default"

FUNCTION_CALL_TYPE = "function_call"
FUNCTION_CALL_OUTPUT_TYPE = "function_call_output"
MESSAGE_TYPE = "message"
REASONING_TYPE = "reasoning"
REASONING_EFFORT_NONE = "none"

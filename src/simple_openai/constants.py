from pathlib import Path


BASE_URL = "https://api.openai.com"
RESPONSES_URL = "/v1/responses"
IMAGE_URL = "/v1/images/generations"

FULL_RESPONSES_URL = BASE_URL + RESPONSES_URL
FULL_IMAGE_URL = BASE_URL + IMAGE_URL

MAX_CHAT_HISTORY = 21
CHAT_HISTORY_FILE = Path("chat_history.json")
DEFAULT_CHAT_ID = "default"
DEFAULT_MODEL = "gpt-5.6-sol"
MAX_OUTPUT_TOKENS = 4096

FUNCTION_CALL_TYPE = "function_call"
FUNCTION_CALL_OUTPUT_TYPE = "function_call_output"
MESSAGE_TYPE = "message"
REASONING_TYPE = "reasoning"
REASONING_EFFORT_LOW = "low"

# gpt-5.6-sol short-context rates (USD per million tokens), 20 Sep 2026.
SOL_INPUT_USD_PER_MILLION = 4.00
SOL_CACHED_INPUT_USD_PER_MILLION = 0.40
SOL_CACHE_WRITE_USD_PER_MILLION = 5.00
SOL_OUTPUT_USD_PER_MILLION = 20.00
PROMPT_CACHE_MODE_EXPLICIT = "explicit"

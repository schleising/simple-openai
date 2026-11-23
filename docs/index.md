# Simple Openai

This is a thin wrapper around the OpenAI API. Chat uses
[`POST /v1/responses`](https://platform.openai.com/docs/api-reference/responses).
Images still use [`POST /v1/images/generations`](https://platform.openai.com/docs/api-reference/images)
(DALL·E 3).

It provides both [synchronous](simple_openai/simple_openai.md) and
[asynchronous](simple_openai/async_simple_openai.md) clients. The default
chat model is `gpt-6.2-sol`.

## Installation

Install using pip:

```bash
pip install git+https://github.com/schleising/simple-openai.git
```

## Usage

### Chat

Pass an API key and a system message. The system message is sent as the first
developer message in `input`, with an explicit prompt-cache breakpoint.
GPT-6.2 appends top-level `instructions` after the conversation and bills
them as uncached input, so the library does not use that field. If you pass
a `storage_path`, chat history is written to `chat_history.json` in that
directory.

!!! Example "Synchronous Version"
    ```python
    from pathlib import Path

    from simple_openai import SimpleOpenai

    def main():
        storage_location = Path("/path/to/storage")
        system_message = (
            "You are a helpful chatbot. You are very friendly and helpful. "
            "You are a good friend to have."
        )

        client = SimpleOpenai(
            api_key,
            system_message,
            storage_location,
            timezone="Europe/London",
        )

        result = client.get_chat_response(
            "Hello, how are you?",
            name="Bob",
            chat_id="Group 1",
        )

        if result.success:
            print(f"Success: {result.message}")
        else:
            print(f"Error: {result.message}")

        result = client.get_image_url("A cat")

        if result.success:
            print(f"Success: {result.message}")
        else:
            print(f"Error: {result.message}")

    if __name__ == "__main__":
        main()
    ```

!!! Example "Asynchronous Version"
    ```python
    import asyncio
    from pathlib import Path

    from simple_openai import AsyncSimpleOpenai

    async def main():
        storage_location = Path("/path/to/storage")
        system_message = (
            "You are a helpful chatbot. You are very friendly and helpful. "
            "You are a good friend to have."
        )

        client = AsyncSimpleOpenai(
            api_key,
            system_message,
            storage_location,
            timezone="Europe/London",
        )

        tasks = [
            client.get_chat_response(
                "Hello, how are you?",
                name="Bob",
                chat_id="Group 1",
            ),
            client.get_image_url("A cat"),
        ]

        for task in asyncio.as_completed(tasks):
            result = await task

            if result.success:
                print(f"Success: {result.message}")
            else:
                print(f"Error: {result.message}")

    if __name__ == "__main__":
        asyncio.run(main())
    ```

`get_chat_response` continues a local transcript for `chat_id` (default
`"default"`). Optional arguments:

- `max_tool_calls` — how many tool rounds to allow for this turn (default `1`)
- `add_date_time` — prefix the date and time onto the latest user message,
  not onto `instructions`. The line is stored once and replayed unchanged,
  so a later request does not edit the prefix. It is not shown in the local
  transcript.
- `model` — override the client default for this call

The speaker `name` is stored locally and sent to the model as
`"{name}: {prompt}"`.

### Output

Chat and image methods return a
[SimpleOpenaiResponse](simple_openai/responses.md#src.simple_openai.responses.SimpleOpenaiResponse):

- `success` — whether the request succeeded
- `message` — assistant text, image URL, or an error string

Check `success` before using `message`.

### Tools

Register local functions with `add_tool`. Pass an
[OpenAITool](simple_openai/public_models.md/#src.simple_openai.models.open_ai_models.OpenAITool)
definition and a Python function that returns a `str`. On the async client the
callback must be awaitable.

The library converts that schema to a Responses function tool. When the model
emits a `function_call`, the function runs and the string result is sent back
as a `function_call_output` item.

```python
from simple_openai.models import open_ai_models

def internet_search(**kwargs: object) -> str:
    return "search results"

client.add_tool(
    open_ai_models.OpenAITool(
        function=open_ai_models.OpenAIFunction(
            name="internet_search",
            description="Search the internet",
            parameters=open_ai_models.OpenAIParameters(properties={}),
        )
    ),
    internet_search,
)
```

### Chat history

Each `chat_id` has its own rolling window of up to 21 Responses items. OpenAI
does not retain the conversation (`store` is `false`). Reasoning items are
kept in that window and sent back with later turns. They are omitted from
the rendered transcript. Older Chat Completions history files are converted
on load.

```python
print(client.get_chat_history("Group 1"))
print(client.get_truncated_chat_history("Group 1"))
client.update_system_message("You are now a pirate.")
```

`AsyncSimpleOpenai` also has `clear_chat(chat_id)`.

### Models and usage

The client default is `gpt-6.2-sol`. You can change it on the constructor or
per chat call:

```python
client = SimpleOpenai(api_key, system_message, model="gpt-6.2-astra")
result = client.get_chat_response("Hello", name="Bob", model="gpt-6.2-sol")
```

Each Responses call logs token counts and a short-context `gpt-6.2-sol` USD
estimate on the `simple_openai.usage` logger. The estimate uses Standard
rates for prompts up to 272K input tokens, with 30-minute cache writes unless
the response reports 12-hour writes. `SimpleOpenaiResponse` still only has
`success` and `message`.

```python
import logging

logging.basicConfig(level=logging.INFO)
```

See [Usage](simple_openai/usage.md) for the estimate helper.

## Documentation

The reference section documents the public classes. Design notes cover the
[gpt-6.2-sol defaults](design/gpt-6.2-sol.md), the Responses migration, and
the earlier gpt-5.6-sol defaults.

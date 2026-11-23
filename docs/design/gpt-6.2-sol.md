# Design: default model gpt-6.2-sol

Shipped in v6.4.0. This replaces the [gpt-5.6-sol defaults](tune-gpt-5.6-sol.md)
as the current client configuration. That earlier note stays as the record
of v6.2.0.

## Model

The client default is `gpt-6.2-sol`. Callers can still pass `model=` on the
constructor or on `get_chat_response`. Chat stays on `POST /v1/responses`.
Images stay on `/v1/images/generations`.

`reasoning.effort` stays `low`. GPT-6.2 Sol rejects `none`. `reasoning.context`
is omitted so the model uses its own default. `temperature` and `top_p` stay
off. `max_output_tokens` stays 4096.

## Prompt cache

`prompt_cache_options` is `{ "mode": "explicit", "ttl": "30m" }`. The system
message is the first developer item in `input`, with an explicit breakpoint.
GPT-6.2 appends top-level `instructions` after the conversation and bills
them as uncached input, so the library does not send that field.

## Reasoning replay

`store` stays `false`. Reasoning items, including `encrypted_content`, are
kept in the local 21-item window and sent back on later turns, including
tool-call follow-ups. They are omitted from the rendered transcript.

When `add_date_time=True`, the date line is written onto the latest user
message once and then replayed unchanged. A fresh timestamp on every HTTP
call would edit the prefix, and GPT-6.2 drops reasoning after that kind of
edit. The line is not shown in `get_chat_history()`.

## Usage log

Each Responses call logs token counts and a USD estimate on
`simple_openai.usage`. Rates are gpt-6.2-sol Standard, short context (at most
272K input tokens), per million tokens:

| | USD |
| --- | ---: |
| Input | 2.00 |
| Cached input | 0.10 |
| Cache write, 30 minutes | 2.50 |
| Cache write, 12 hours | 5.00 |
| Output, including reasoning | 10.00 |

`output_tokens` already includes reasoning tokens. Cached tokens and cache
writes are portions of `input_tokens`. A write is priced at the 30-minute
rate unless the response reports `ttl_12h_tokens`. Prompts above 272K input
tokens use OpenAI’s long-context rates; the log assumes short context.

"""OpenAI API models

This module contains the models for the OpenAI API.

The models are used to validate the data sent to and received from the OpenAI API.

The models are based on the [OpenAI API documentation](https://platform.openai.com/docs/api-reference/responses) and use [Pydantic](https://docs.pydantic.dev/) to help serialise and deserialise the JSON.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

from simple_openai.constants import (
    DEFAULT_MODEL,
    FUNCTION_CALL_OUTPUT_TYPE,
    FUNCTION_CALL_TYPE,
    MAX_CHAT_HISTORY,
    MAX_OUTPUT_TOKENS,
    MESSAGE_TYPE,
    REASONING_EFFORT_LOW,
    REASONING_TYPE,
)

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class OpenAIParameter(BaseModel):
    """OpenAI parameter

    This class represents an OpenAI parameter.

    Attributes:
        type (str | None): The JSON schema type of the parameter
        description (str | None): The description used by OpenAI when choosing tools
        properties (dict[str, OpenAIParameter] | None): Nested object properties
        required (list[str] | None): Required nested properties
        items (OpenAIParameter | None): Array item schema
        enum (list[JsonScalar] | None): Enum values for constrained fields
        default (JsonScalar | None): Default value for the parameter
        pattern (str | None): Regex pattern for string values
        minimum (int | float | None): Minimum numeric value
        maximum (int | float | None): Maximum numeric value
        additionalProperties (bool | OpenAIParameter | None): Whether extra properties are allowed
    """

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    description: str | None = None
    properties: dict[str, OpenAIParameter] | None = None
    required: list[str] | None = None
    items: OpenAIParameter | None = None
    enum: list[JsonScalar] | None = None
    default: JsonScalar | None = None
    pattern: str | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    additionalProperties: bool | OpenAIParameter | None = None


class OpenAIParameters(BaseModel):
    """OpenAI parameters

    This class represents a list of OpenAI parameters.

    Attributes:
        type (str): The type of the parameters
        properties (dict[str, OpenAIParameter]): The parameters
        required (list[str], optional): The required parameters. Defaults to [].
        additionalProperties (bool | OpenAIParameter | None): Whether extra properties are allowed
    """

    model_config = ConfigDict(extra="allow")

    type: str = "object"
    properties: dict[str, OpenAIParameter]
    required: list[str] = []
    additionalProperties: bool | OpenAIParameter | None = None


class OpenAIFunction(BaseModel):
    """OpenAI function

    This class represents an OpenAI function.

    Attributes:
        name (str): The name of the function
        description (str): The description of the function, used by OpenAI to decide whether to use the function
        parameters (OpenAIParameters): The parameters of the function
    """

    name: str
    description: str
    parameters: OpenAIParameters


class OpenAITool(BaseModel):
    """Tool definition used by `add_tool`

    This is the Chat Completions-shaped public schema. It is converted to a
    Responses function tool when a request is sent.
    """

    type: str = "function"
    function: OpenAIFunction


OpenAIParameter.model_rebuild()


class ResponsesFunctionTool(BaseModel):
    """Function tool in the internally tagged Responses format"""

    type: str = "function"
    name: str
    description: str
    parameters: OpenAIParameters
    strict: bool = False

    @classmethod
    def from_openai_tool(cls, tool: OpenAITool) -> ResponsesFunctionTool:
        """Convert a public `OpenAITool` to a Responses function tool"""
        return cls(
            name=tool.function.name,
            description=tool.function.description,
            parameters=tool.function.parameters,
            strict=False,
        )


class FunctionCall(BaseModel):
    """Legacy Chat Completions function call"""

    name: str
    arguments: str


class ToolCall(BaseModel):
    """Legacy Chat Completions tool call"""

    id: str
    type: str
    function: FunctionCall


class ChatMessage(BaseModel):
    """Legacy Chat Completions message stored in older history files"""

    role: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    content: str | None = None
    name: str = "Botto"


class ContentPart(BaseModel):
    """A typed text part inside a Responses message"""

    model_config = ConfigDict(extra="allow")

    type: str
    text: str | None = None


class InputItem(BaseModel):
    """A Responses input or output item

    Unknown fields are kept so extra Responses metadata can round-trip.
    Reasoning items are not sent back to the API.

    `speaker` is local display metadata and is not sent to OpenAI.
    """

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    role: str | None = None
    content: str | list[ContentPart] | None = None
    name: str | None = None
    call_id: str | None = None
    arguments: str | None = None
    output: str | None = None
    status: str | None = None
    id: str | None = None
    speaker: str | None = None

    def is_reasoning(self) -> bool:
        """Whether this item is a reasoning payload that should not be replayed"""
        return self.type == REASONING_TYPE

    def display_name(self) -> str:
        """Name used when rendering the local transcript"""
        if self.speaker:
            return self.speaker
        if self.role == "user":
            return "user"
        return "Botto"

    def display_text(self) -> str | None:
        """Plain text for the local transcript, if this item has any"""
        if self.type == FUNCTION_CALL_OUTPUT_TYPE:
            return self.output
        if self.type == FUNCTION_CALL_TYPE:
            return None

        content = self.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [part.text for part in content if part.text]
            return "".join(parts) if parts else None
        return None

    def to_api_item(self) -> InputItem:
        """Return a copy of this item suitable for a Responses `input` array"""
        if self.type in {None, MESSAGE_TYPE} and self.role == "user":
            content = self.content
            if self.speaker and isinstance(content, str):
                content = f"{self.speaker}: {content}"
            return InputItem(type=MESSAGE_TYPE, role="user", content=content)
        if self.type == FUNCTION_CALL_OUTPUT_TYPE:
            return InputItem(
                type=FUNCTION_CALL_OUTPUT_TYPE,
                call_id=self.call_id,
                output=self.output or "",
            )
        return InputItem.model_validate(
            self.model_dump(exclude_none=True, exclude={"speaker"})
        )


class ChatContext(BaseModel):
    """Instructions and input items for the next Responses request"""

    instructions: str
    input: list[InputItem]


class ChatHistory(BaseModel):
    messages: dict[str, deque[InputItem]]

    @field_validator("messages", mode="before")
    @classmethod
    def convert_legacy_messages(
        cls, value: object
    ) -> dict[str, list[InputItem]] | object:
        if not isinstance(value, dict):
            return value

        converted: dict[str, list[InputItem]] = {}
        for chat_id, items in value.items():
            if not isinstance(items, (list, tuple, deque)):
                raise TypeError(
                    f"Chat history for {chat_id!r} must be a sequence of items"
                )
            converted_items: list[InputItem] = []
            for item in items:
                converted_items.extend(coerce_history_item(item))
            converted[str(chat_id)] = converted_items
        return converted

    @field_validator("messages", mode="after")
    @classmethod
    def enforce_maxlen(
        cls, value: dict[str, deque[InputItem]]
    ) -> dict[str, deque[InputItem]]:
        return {key: deque(items, maxlen=MAX_CHAT_HISTORY) for key, items in value.items()}


class ReasoningConfig(BaseModel):
    """Reasoning settings for the Responses API"""

    effort: str = REASONING_EFFORT_LOW


class ResponsesRequest(BaseModel):
    """Request body for `POST /v1/responses`"""

    model: str = DEFAULT_MODEL
    input: list[InputItem]
    instructions: str | None = None
    tools: list[ResponsesFunctionTool] | None = None
    tool_choice: str | None = None
    parallel_tool_calls: bool | None = None
    store: bool = False
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    max_output_tokens: int = MAX_OUTPUT_TOKENS


class InputTokensDetails(BaseModel):
    """Input-token breakdown from a Responses `usage` object"""

    model_config = ConfigDict(extra="allow")

    cached_tokens: int = 0


class OutputTokensDetails(BaseModel):
    """Output-token breakdown from a Responses `usage` object"""

    model_config = ConfigDict(extra="allow")

    reasoning_tokens: int = 0


class ResponsesUsage(BaseModel):
    """Token usage from a Responses API body"""

    model_config = ConfigDict(extra="allow")

    input_tokens: int = 0
    input_tokens_details: InputTokensDetails | None = None
    output_tokens: int = 0
    output_tokens_details: OutputTokensDetails | None = None
    total_tokens: int = 0

    @property
    def cached_tokens(self) -> int:
        """Cached input tokens, or 0 if the API omitted the breakdown"""
        if self.input_tokens_details is None:
            return 0
        return self.input_tokens_details.cached_tokens

    @property
    def reasoning_tokens(self) -> int:
        """Reasoning tokens billed as output, or 0 if omitted"""
        if self.output_tokens_details is None:
            return 0
        return self.output_tokens_details.reasoning_tokens


class ResponsesResult(BaseModel):
    """Response body from `POST /v1/responses`"""

    model_config = ConfigDict(extra="allow")

    id: str
    output: list[InputItem] = []
    usage: ResponsesUsage | None = None

    def function_calls(self) -> list[InputItem]:
        """Function call items from this response"""
        return [item for item in self.output if item.type == FUNCTION_CALL_TYPE]

    def output_text(self) -> str:
        """Concatenated assistant text, matching the Responses SDK helper"""
        parts: list[str] = []
        for item in self.output:
            if item.type != MESSAGE_TYPE:
                continue
            text = item.display_text()
            if text:
                parts.append(text)
        return "".join(parts)


class ImageRequest(BaseModel):
    model: str = "dall-e-3"
    prompt: str
    n: int = 1
    size: str = "1024x1024"
    response_format: str = "url"
    quality: str = "hd"
    style: str = "vivid"


class Url(BaseModel):
    url: str


class ImageResponse(BaseModel):
    created: int
    data: list[Url]


class Error(BaseModel):
    code: str | None
    message: str
    param: str | None
    type: str


class ErrorResponse(BaseModel):
    error: Error


def as_json_value(value: object) -> JsonValue:
    """Convert a parsed JSON value into a typed JSON value"""
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, list):
        return [as_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_json_value(item) for key, item in value.items()}
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def as_json_object(value: object) -> dict[str, JsonValue]:
    """Convert a parsed JSON object into a typed JSON object"""
    if not isinstance(value, dict):
        raise ValueError("Tool arguments must be a JSON object")
    return {str(key): as_json_value(item) for key, item in value.items()}


def coerce_history_item(item: object) -> list[InputItem]:
    """Convert a stored history value into Responses input items

    Older `chat_history.json` files used Chat Completions messages. Those are
    expanded into `function_call` / `function_call_output` / `message` items.
    """
    if isinstance(item, InputItem):
        if _is_legacy_completions_item(item):
            return _legacy_message_to_items(
                ChatMessage(
                    role=item.role or "assistant",
                    tool_calls=_legacy_tool_calls(item),
                    tool_call_id=item.call_id,
                    content=item.content if isinstance(item.content, str) else None,
                    name=item.speaker or item.name or "Botto",
                )
            )
        return [item]

    if isinstance(item, ChatMessage):
        return _legacy_message_to_items(item)

    if isinstance(item, BaseModel):
        return coerce_history_item(item.model_dump(exclude_none=True))

    if not isinstance(item, dict):
        raise TypeError(f"Unsupported chat history item: {type(item)!r}")

    payload: dict[str, object] = {str(key): value for key, value in item.items()}
    if _is_legacy_completions_dict(payload):
        return _legacy_message_to_items(ChatMessage.model_validate(payload))

    if "speaker" not in payload and payload.get("role") == "user":
        name = payload.get("name")
        if isinstance(name, str):
            payload["speaker"] = name
    return [InputItem.model_validate(payload)]


def _is_legacy_completions_item(item: InputItem) -> bool:
    return item.type is None and item.role in {"user", "assistant", "tool", "system"}


def _is_legacy_completions_dict(item: Mapping[str, object]) -> bool:
    item_type = item.get("type")
    if isinstance(item_type, str) and item_type:
        return False
    return item.get("role") in {"user", "assistant", "tool", "system"}


def _legacy_tool_calls(item: InputItem) -> list[ToolCall] | None:
    extra = item.model_extra
    if extra is None:
        return None
    tool_calls = extra.get("tool_calls")
    if not isinstance(tool_calls, Sequence) or isinstance(tool_calls, (str, bytes)):
        return None
    return [ToolCall.model_validate(tool_call) for tool_call in tool_calls]


def _legacy_message_to_items(message: ChatMessage) -> list[InputItem]:
    if message.role == "system":
        return []

    if message.role == "tool":
        return [
            InputItem(
                type=FUNCTION_CALL_OUTPUT_TYPE,
                call_id=message.tool_call_id,
                output=message.content or "",
            )
        ]

    if message.role == "assistant" and message.tool_calls:
        return [
            InputItem(
                type=FUNCTION_CALL_TYPE,
                call_id=tool_call.id,
                name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            )
            for tool_call in message.tool_calls
        ]

    return [
        InputItem(
            type=MESSAGE_TYPE,
            role=message.role,
            content=message.content,
            speaker=message.name,
        )
    ]

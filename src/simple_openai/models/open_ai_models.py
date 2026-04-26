"""OpenAI API models

This module contains the models for the OpenAI API.

The models are used to validate the data sent to and received from the OpenAI API.

The models are based on the [OpenAI API documentation](https://beta.openai.com/docs/api-reference/introduction) and use [Pydantic](https://pydantic-docs.helpmanual.io/) to help serialise and deserialise the JSON.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from simple_openai.constants import MAX_CHAT_HISTORY


class OpenAIParameter(BaseModel):
    """OpenAI parameter

    This class represents an OpenAI parameter.

    Attributes:
        type (str | None): The JSON schema type of the parameter
        description (str | None): The description used by OpenAI when choosing tools
        properties (dict[str, OpenAIParameter] | None): Nested object properties
        required (list[str] | None): Required nested properties
        items (OpenAIParameter | None): Array item schema
        enum (list[Any] | None): Enum values for constrained fields
        default (Any | None): Default value for the parameter
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
    enum: list[Any] | None = None
    default: Any | None = None
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
    type: str = "function"
    function: OpenAIFunction


OpenAIParameter.model_rebuild()


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: FunctionCall


class ChatMessage(BaseModel):
    role: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    content: str | None = None
    name: str = "Botto"


class Chat(BaseModel):
    messages: list[ChatMessage]


class ChatHistory(BaseModel):
    messages: dict[str, deque[ChatMessage]]

    # Ensure maxlen is always enforced
    @field_validator("messages", mode="after")
    def enforce_maxlen(cls, v: dict[str, deque[ChatMessage]]) -> dict[str, deque[ChatMessage]]:
        # Always reconstruct with maxlen=MAX_CHAT_HISTORY
        return {k: deque(v, maxlen=MAX_CHAT_HISTORY) for k, v in v.items()}


class ChatRequest(Chat):
    tools: list[OpenAITool] | None = None
    tool_choice: str
    model: str = "gpt-5.5"
    parallel_tool_calls: bool = False


class ResponseMessage(BaseModel):
    role: str
    content: str | None
    tool_calls: list[ToolCall] | None = None


class Choice(BaseModel):
    index: int
    message: ResponseMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    choices: list[Choice]
    usage: Usage


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

""" OpenAI API models

This module contains the models for the OpenAI API.

The models are used to validate the data sent to and received from the OpenAI API.

The models are based on the [OpenAI API documentation](https://beta.openai.com/docs/api-reference/introduction) and use [Pydantic](https://pydantic-docs.helpmanual.io/) to help serialise and deserialise the JSON.
"""

from pydantic import BaseModel


class OpenAIParameter(BaseModel):
    """OpenAI parameter

    This class represents an OpenAI parameter.

    Attributes:
        type (str): The type of the parameter
        description (str): The description of the parameter, used by OpenAI to decide whether to use the parameter
    """

    type: str
    description: str


class OpenAIParameters(BaseModel):
    """OpenAI parameters

    This class represents a list of OpenAI parameters.

    Attributes:
        type (str): The type of the parameters
        properties (dict[str, OpenAIParameter]): The parameters
        required (list[str], optional): The required parameters. Defaults to [].
    """

    type: str = "object"
    properties: dict[str, OpenAIParameter]
    required: list[str] = []


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


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: FunctionCall


class ChatMessage(BaseModel):
    role: str
    content: str
    name: str = "Botto"


class Chat(BaseModel):
    messages: list[ChatMessage]


class ChatRequest(Chat):
    tools: list[OpenAITool] | None = None
    tool_choice: str
    model: str = "gpt-4o"


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

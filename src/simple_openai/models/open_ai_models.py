from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str = 'user'
    content: str

class ChatRequest(BaseModel):
    model: str = 'gpt-4'
    messages: list[ChatMessage]

class Choice(BaseModel):
    index: int
    message: ChatMessage
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
    prompt: str
    n: int = 1
    size: str = '1024x1024'
    response_format: str = 'url'

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

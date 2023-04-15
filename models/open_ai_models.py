from pydantic import BaseModel

class Message(BaseModel):
    role: str = 'user'
    content: str

class Request(BaseModel):
    model: str = 'gpt-3.5-turbo'
    messages: list[Message]

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class Response(BaseModel):
    id: str
    object: str
    created: int
    choices: list[Choice]
    usage: Usage

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from enum import Enum


class ModelName(str, Enum):
    """Supported Groq model names."""
    LLAMA_3_1_8B_INSTANT = "llama-3.1-8b-instant"
    GPT_OSS_120B = "openai/gpt-oss-120b"
    QWEN3_32B = "qwen/qwen3-32b"
    GROQ_COMPOUND = "groq/compound"


class Hyperparameters(BaseModel):
    """Hyperparameters for LLM generation."""
    
    temperature: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Controls randomness. Lower = more deterministic, Higher = more creative"
    )
    top_p: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold"
    )
    max_tokens: Optional[int] = Field(
        default=1024,
        ge=1,
        le=32000,
        description="Maximum tokens to generate"
    )
    stop: Optional[List[str]] = Field(
        default=None,
        max_length=4,
        description="Stop sequences (max 4)"
    )
    
    @field_validator('stop')
    @classmethod
    def validate_stop_sequences(cls, v):
        """Validate stop sequences."""
        if v is not None and len(v) > 4:
            raise ValueError("Maximum 4 stop sequences allowed")
        return v


class ChatMessage(BaseModel):
    """A single chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    
    model: ModelName = Field(
        description="Model to use for generation"
    )
    user_prompt: str = Field(
        min_length=1,
        description="User's input prompt"
    )
    system_prompt: Optional[str] = Field(
        default="You are a helpful AI assistant.",
        description="System prompt to guide model behavior"
    )
    hyperparameters: Optional[Hyperparameters] = Field(
        default_factory=Hyperparameters,
        description="Generation hyperparameters"
    )
    save_conversation: bool = Field(
        default=False,
        description="Whether to save conversation history"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID for continuing an existing conversation"
    )
    
    def to_messages(self, conversation_history: Optional[List[ChatMessage]] = None) -> dict:
        """Convert request to LangChain-compatible payload."""
        messages = []

        if conversation_history:
            messages.extend([msg.model_dump() for msg in conversation_history])
        
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": self.user_prompt
        })
        
        payload = {
            "model": self.model.value,
            "messages": messages,
            "stream": True
        }
        
        if self.hyperparameters:
            params = self.hyperparameters.model_dump(exclude_none=True)
            payload.update(params)
        
        return payload


class StreamResponse(BaseModel):
    """Streaming response chunk."""
    content: str
    finished: bool = False
    conversation_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    model: Optional[str] = None

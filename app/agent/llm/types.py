from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token accounting across prompt, completion, and total."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCall(BaseModel):
    """Canonical normalized tool invocation requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Canonical model response across any LLM provider."""
    text: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: str = "stop"  # "stop", "tool_call", "length", "safety", "error"
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: Optional[str] = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMChunk(BaseModel):
    """Incremental chunk emitted during streaming responses."""
    delta_text: Optional[str] = None
    delta_tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: Optional[str] = None

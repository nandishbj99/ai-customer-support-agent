from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import AgentOrchestrator, AgentResult
from app.agent.state import SessionStateManager

router = APIRouter(prefix="/chat", tags=["Chat"])

# Shared singleton session manager
_session_manager = SessionStateManager()


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for the conversation")
    customer_id: str = Field(..., description="Authenticated customer identifier")
    message: str = Field(..., min_length=1, description="Customer message text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional conversation metadata")


class ChatMessageResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    status: str
    confidence_score: float
    escalated: bool
    tool_calls_made: List[str]


def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator(session_manager=_session_manager)


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> ChatMessageResponse:
    """Process a customer message through the agent orchestrator and ReAct loop."""
    try:
        result: AgentResult = await orchestrator.run(
            session_id=payload.session_id,
            customer_id=payload.customer_id,
            message=payload.message,
        )
        return ChatMessageResponse(
            session_id=result.session_id,
            message_id=result.message_id,
            response=result.response,
            status=result.status,
            confidence_score=result.confidence_score,
            escalated=result.escalated,
            tool_calls_made=result.tool_calls_made,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal agent error: {str(e)}")

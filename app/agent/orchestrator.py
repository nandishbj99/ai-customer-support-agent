import asyncio
import uuid
from typing import Any, Dict, List, Optional
import structlog
from pydantic import BaseModel, Field

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.factory import LLMProviderFactory
from app.agent.prompts import FINTECH_AGENT_SYSTEM_PROMPT
from app.agent.state import SessionStateManager
from app.agent.tool_router import ToolRouter
from app.tools.registry import ToolRegistry

logger = structlog.get_logger()


class AgentResult(BaseModel):
    """Result payload returned by the Agent Orchestrator."""
    session_id: str
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:10]}")
    response: str
    status: str = "success"  # "success", "escalated", "fallback", "error"
    confidence_score: float = 0.95
    escalated: bool = False
    tool_calls_made: List[str] = Field(default_factory=list)
    iterations: int = 0


class AgentOrchestrator:
    """Core ReAct loop orchestrator integrating LLM provider with ToolRouter."""

    def __init__(
        self,
        llm_provider: Optional[LLMProviderBase] = None,
        tool_router: Optional[ToolRouter] = None,
        session_manager: Optional[SessionStateManager] = None,
        system_prompt: str = FINTECH_AGENT_SYSTEM_PROMPT,
        max_iterations: int = 5,
        max_tool_calls: int = 10,
        timeout_seconds: float = 30.0,
    ):
        self.llm_provider = llm_provider or LLMProviderFactory.create()
        if tool_router is not None:
            self.tool_router = tool_router
        else:
            from app.tools.factory import ToolServiceFactory
            services = ToolServiceFactory.create_services()
            self.tool_router = ToolRouter(services=services)
        self.session_manager = session_manager
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.timeout_seconds = timeout_seconds

    async def _finalize(
        self,
        session_id: str,
        customer_id: str,
        result: AgentResult,
        messages: List[Dict[str, Any]],
    ) -> AgentResult:
        if self.session_manager:
            try:
                session = await self.session_manager.get_or_create_session(session_id, customer_id)
                session.messages = messages + [{"role": "assistant", "content": result.response}]
                await self.session_manager.save_session(session)
            except Exception as e:
                logger.warn("session_save_failed", session_id=session_id, error=str(e))
        return result

    async def run(
        self,
        session_id: str,
        customer_id: str,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentResult:
        """Execute the ReAct loop for a single customer turn."""
        if history is not None:
            messages = list(history)
        elif self.session_manager:
            session = await self.session_manager.get_or_create_session(session_id, customer_id)
            messages = list(session.messages)
        else:
            messages = []
        messages.append({"role": "user", "content": message})

        tools_schema = ToolRegistry.get_gemini_function_declarations()
        tool_calls_made: List[str] = []
        escalated = False

        # PROMPT INJECTION DEFENSE (FR-13, ADR-04)
        from app.security.prompt_guard import InjectionRiskLevel, prompt_guard
        assessment = prompt_guard.evaluate(message)
        if assessment.risk_level == InjectionRiskLevel.BLOCKED:
            logger.warn(
                "prompt_injection_blocked",
                session_id=session_id,
                customer_id=customer_id,
                patterns=assessment.matched_patterns,
            )
            return await self._finalize(
                session_id,
                customer_id,
                AgentResult(
                    session_id=session_id,
                    response=assessment.rejection_message or "Request blocked due to security policy violation.",
                    status="blocked",
                    confidence_score=1.0,
                    escalated=False,
                    iterations=0,
                ),
                messages,
            )

        for iteration in range(self.max_iterations):
            try:
                llm_response = await asyncio.wait_for(
                    self.llm_provider.generate(
                        messages=messages,
                        tools=tools_schema,
                        system_instruction=self.system_prompt,
                    ),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.error("llm_call_timeout", session_id=session_id, iteration=iteration)
                return await self._finalize(
                    session_id,
                    customer_id,
                    AgentResult(
                        session_id=session_id,
                        response="I am experiencing a slight delay connecting to our core systems. Let me transfer you to a human representative who can assist immediately.",
                        status="fallback",
                        confidence_score=0.3,
                        escalated=True,
                        tool_calls_made=tool_calls_made,
                        iterations=iteration + 1,
                    ),
                    messages,
                )
            except Exception as e:
                logger.error("llm_call_failed", session_id=session_id, error=str(e))
                return await self._finalize(
                    session_id,
                    customer_id,
                    AgentResult(
                        session_id=session_id,
                        response="I encountered an unexpected issue retrieving your account details. A human support specialist has been notified to assist you.",
                        status="error",
                        confidence_score=0.2,
                        escalated=True,
                        tool_calls_made=tool_calls_made,
                        iterations=iteration + 1,
                    ),
                    messages,
                )

            if llm_response.has_tool_calls:
                # Add assistant thought / tool invocation to conversation
                messages.append({
                    "role": "model",
                    "content": llm_response.text or "",
                    "tool_calls": llm_response.tool_calls,
                })

                for tc in llm_response.tool_calls:
                    if len(tool_calls_made) >= self.max_tool_calls:
                        logger.warn("max_tool_calls_exceeded", count=len(tool_calls_made))
                        escalated = True
                        break

                    tool_calls_made.append(tc.name)
                    if tc.name == "escalateToHumanAgent":
                        escalated = True

                    logger.info("executing_tool", tool=tc.name, session_id=session_id)
                    tool_result = await self.tool_router.execute(
                        tool_name=tc.name,
                        arguments=tc.arguments,
                        session_user_id=customer_id,
                        session_id=session_id,
                    )

                    messages.append({
                        "role": "tool",
                        "name": tc.name,
                        "content": tool_result.model_dump(),
                    })

                if len(tool_calls_made) >= self.max_tool_calls:
                    return await self._finalize(
                        session_id,
                        customer_id,
                        AgentResult(
                            session_id=session_id,
                            response="This request requires extensive investigation. I have connected you to our senior support team.",
                            status="escalated",
                            confidence_score=0.5,
                            escalated=True,
                            tool_calls_made=tool_calls_made,
                            iterations=iteration + 1,
                        ),
                        messages,
                    )
            else:
                # Final response reached
                final_text = llm_response.text or "Thank you for contacting customer support. How else may I assist you?"
                confidence = 0.95 if not escalated else 0.70

                logger.info(
                    "react_loop_completed",
                    session_id=session_id,
                    iterations=iteration + 1,
                    tool_calls_count=len(tool_calls_made),
                )
                return await self._finalize(
                    session_id,
                    customer_id,
                    AgentResult(
                        session_id=session_id,
                        response=final_text,
                        status="escalated" if escalated else "success",
                        confidence_score=confidence,
                        escalated=escalated,
                        tool_calls_made=tool_calls_made,
                        iterations=iteration + 1,
                    ),
                    messages,
                )

        # Reached max iterations without final answer
        logger.warn("max_iterations_exhausted", session_id=session_id)
        return await self._finalize(
            session_id,
            customer_id,
            AgentResult(
                session_id=session_id,
                response="I was unable to complete the investigation within the allotted steps. I am escalating your case to a human support agent.",
                status="fallback",
                confidence_score=0.4,
                escalated=True,
                tool_calls_made=tool_calls_made,
                iterations=self.max_iterations,
            ),
            messages,
        )

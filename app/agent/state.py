from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import structlog
from pydantic import BaseModel, Field

from app.core.config import settings

logger = structlog.get_logger()


class SessionState(BaseModel):
    """Hot session state stored in Redis or memory cache."""
    session_id: str
    customer_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionStateManager:
    """Manages multi-turn conversation state with Redis and local fallback."""

    def __init__(self, redis_url: Optional[str] = None, max_messages: int = 20):
        self.redis_url = redis_url or settings.REDIS_URL
        self.max_messages = max_messages
        self._memory_store: Dict[str, SessionState] = {}
        self._redis_client = None

    async def _get_redis(self):
        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis
                client = aioredis.from_url(self.redis_url, decode_responses=True)
                # Quick ping to verify connectivity
                await client.ping()
                self._redis_client = client
            except Exception as e:
                logger.debug("redis_connection_unavailable_using_memory", error=str(e))
                self._redis_client = False
        return self._redis_client if self._redis_client is not False else None

    def truncate_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maintain a sliding window of recent messages to stay well within context limits."""
        if len(messages) <= self.max_messages:
            return messages
        # Keep the earliest message if it was a system message, then take the last N messages
        first_msg = messages[0] if messages and messages[0].get("role") == "system" else None
        recent = messages[-self.max_messages:]
        if first_msg and recent and recent[0] != first_msg:
            return [first_msg] + recent[1:]
        return recent

    async def get_session(self, session_id: str) -> Optional[SessionState]:
        redis_client = await self._get_redis()
        if redis_client:
            try:
                raw = await redis_client.get(f"session:{session_id}")
                if raw:
                    return SessionState.model_validate_json(raw)
            except Exception as e:
                logger.warn("redis_get_failed_fallback_memory", session_id=session_id, error=str(e))

        return self._memory_store.get(session_id)

    async def save_session(self, session: SessionState, ttl_seconds: int = 3600) -> None:
        session.updated_at = datetime.now(timezone.utc).isoformat()
        session.messages = self.truncate_history(session.messages)

        redis_client = await self._get_redis()
        if redis_client:
            try:
                payload = session.model_dump_json()
                await redis_client.set(f"session:{session.session_id}", payload, ex=ttl_seconds)
            except Exception as e:
                logger.warn("redis_save_failed_fallback_memory", session_id=session.session_id, error=str(e))

        self._memory_store[session.session_id] = session

    async def get_or_create_session(
        self,
        session_id: str,
        customer_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        session = await self.get_session(session_id)
        if not session:
            session = SessionState(
                session_id=session_id,
                customer_id=customer_id,
                metadata=metadata or {},
            )
            await self.save_session(session)
        return session

    async def append_message(
        self,
        session_id: str,
        message: Dict[str, Any],
        customer_id: str = "guest",
        ttl_seconds: int = 3600,
    ) -> SessionState:
        session = await self.get_or_create_session(session_id, customer_id)
        session.messages.append(message)
        await self.save_session(session, ttl_seconds=ttl_seconds)
        return session

    async def clear_session(self, session_id: str) -> None:
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.delete(f"session:{session_id}")
            except Exception as e:
                logger.warn("redis_delete_failed", session_id=session_id, error=str(e))
        self._memory_store.pop(session_id, None)

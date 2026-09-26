from typing import Any, Dict, List, Optional

from app.rag.knowledge import PolicyKnowledgeService
from app.tools.base import PolicyServiceBase
from app.tools.schemas import ToolResult


class MockPolicyService(PolicyServiceBase):
    """Knowledge base policy search service backed by Hybrid RAG."""

    def __init__(self, knowledge_service: Optional[PolicyKnowledgeService] = None):
        self.knowledge_service = knowledge_service or PolicyKnowledgeService()
        self._seeded = False

    async def _ensure_seeded(self) -> None:
        if not self._seeded and self.knowledge_service.vector_store.count() == 0:
            await self.knowledge_service.seed_default_policies()
            self._seeded = True

    async def search_policy(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3,
    ) -> ToolResult:
        await self._ensure_seeded()

        try:
            results = await self.knowledge_service.search_policies(
                query=query,
                top_k=top_k,
                category=category,
            )

            formatted_snippets = []
            for r in results:
                formatted_snippets.append({
                    "title": r.get("source", {}).get("title", "Policy"),
                    "category": r.get("source", {}).get("category", "general"),
                    "snippet": r.get("text", "")[:400],
                    "relevance_score": r.get("rrf_score", 0.0),
                })

            return ToolResult.ok({
                "query": query,
                "matches": formatted_snippets,
                "results": formatted_snippets,
                "total_found": len(formatted_snippets),
            })
        except Exception as e:
            return ToolResult.fail("POLICY_SEARCH_FAILED", f"Policy search error: {str(e)}")

from contextlib import asynccontextmanager
from fastapi import FastAPI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", environment=settings.ENVIRONMENT, tool_mode=settings.TOOL_MODE)
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="Fintech AI Customer Support Agent",
    description="Autonomous Agentic Customer Support with Deterministic Fintech Tools, RAG, and HITL",
    version="0.1.0",
    lifespan=lifespan,
)


from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.approvals import router as approvals_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.security.middleware import (
    RequestResponseLoggingMiddleware,
    SecurityHeadersMiddleware,
)

# CORS Middleware (FR-11)
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Security Headers & Logging Middlewares (FR-08, FR-12)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestResponseLoggingMiddleware)

# API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "tool_mode": settings.TOOL_MODE,
    }

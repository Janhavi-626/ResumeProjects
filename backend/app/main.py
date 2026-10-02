import logging
import os
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_agents, routes_approval, routes_chat, routes_documents, routes_health, routes_workflows
from app.config.settings import get_settings
from app.models.database import init_db

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(message)s")
structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])
json_formatter = structlog.stdlib.ProcessorFormatter(
    processor=structlog.processors.JSONRenderer(),
    foreign_pre_chain=[structlog.processors.TimeStamper(fmt="iso"), structlog.stdlib.add_log_level, structlog.stdlib.ExtraAdder()],
)
for handler in logging.getLogger().handlers:
    handler.setFormatter(json_formatter)
if settings.langchain_api_key and settings.langchain_tracing_v2:
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", description="Tool-grounded, approval-gated returns investigations.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.getLogger("returns.api").exception("request failed", extra={"request_id": request_id, "path": request.url.path})
        response = JSONResponse(status_code=500, content={"detail": "The request could not be completed.", "request_id": request_id})
    response.headers["X-Request-ID"] = request_id
    return response


for route in (routes_chat, routes_agents, routes_documents, routes_workflows, routes_approval, routes_health):
    app.include_router(route.router, prefix=settings.api_prefix)
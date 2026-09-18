from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.ai.embeddings import get_embedding_provider
from app.ai.llm import get_llm_provider
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.knowledge.seed import seed_all
from app.models import evidence as _evidence_models  # noqa: F401  (ensure models registered)
from app.models import intervention as _intervention_models  # noqa: F401
from app.models import knowledge as _knowledge_models  # noqa: F401
from app.models import monitoring as _monitoring_models  # noqa: F401
from app.models import recommendation as _recommendation_models  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ecosynapse")

settings = get_settings()


class MaxBodySizeMiddleware:
    """Enforces a hard request-body size cap at the ASGI level.

    Checking only the Content-Length header (the naive approach) is
    bypassable: a client can omit it entirely with chunked transfer
    encoding, or simply lie. This buffers incoming body chunks and counts
    real bytes received, rejecting with 413 as soon as the cap is exceeded
    -- before the request ever reaches a route handler.
    """

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        buffered: list[dict] = []
        total = 0
        too_large = False

        while True:
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                buffered.append(message)
                if total > self.max_bytes:
                    too_large = True
                    break
                if not message.get("more_body", False):
                    break
            else:
                buffered.append(message)
                break

        if too_large:
            response = JSONResponse(status_code=413, content={"detail": "Request body too large"})
            await response(scope, receive, send)
            return

        iterator = iter(buffered)

        async def replay_receive():
            try:
                return next(iterator)
            except StopIteration:
                return await receive()

        await self.app(scope, replay_receive, send)


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """Basic single-process, in-memory sliding-window rate limiter per client
    IP. This is a documented, deliberately simple implementation: it resets
    on restart and does not coordinate across multiple instances. Adequate
    for a single-instance demo/hackathon deployment; a production
    multi-instance deployment would need a shared store (e.g. Redis) --
    noted as a known limitation rather than silently pretending this scales.
    """

    def __init__(self, app, requests_per_minute: int):
        super().__init__(app)
        self.limit = requests_per_minute
        self.window_seconds = 60.0
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/health/ready") or self.limit <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[client_ip]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down and try again shortly."},
            )
        hits.append(now)
        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID and logs method/path/status/latency for every
    request -- the minimum viable observability for diagnosing production
    issues without a dedicated APM tool."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start) * 1000
            logger.exception(
                "request_id=%s method=%s path=%s duration_ms=%.1f status=unhandled_exception",
                request_id, request.method, request.url.path, duration_ms,
            )
            raise
        duration_ms = (time.monotonic() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id, request.method, request.url.path, response.status_code, duration_ms,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    except Exception:
        logger.exception("Seed step failed; continuing without seed data")
    finally:
        db.close()
    logger.info(
        "EcoSynapse AI backend started (env=%s, llm=%s, embeddings=%s)",
        settings.environment, get_llm_provider().name, type(get_embedding_provider()).__name__,
    )
    yield


app = FastAPI(
    title=settings.app_name,
    description="Evidence-grounded ecological intelligence and intervention planning API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(InMemoryRateLimiter, requests_per_minute=settings.rate_limit_per_minute)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ASGI-level middleware must wrap the whole stack last so it sees the raw
# body before Starlette's routing/CORS layers touch it.
app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.max_request_body_bytes)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled error request_id=%s on %s %s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


@app.get("/health")
def health():
    """Liveness + informational status. Always returns 200 unless the
    process itself is unresponsive; reports degraded sub-systems in the body
    rather than failing outright, so a transient DB hiccup doesn't take the
    whole health check down for orchestrators using this as a liveness probe."""
    db = SessionLocal()
    try:
        from app.models.evidence import ScientificSource
        from app.models.knowledge import KnowledgeEdge, KnowledgeNode

        source_count = db.query(ScientificSource).count()
        node_count = db.query(KnowledgeNode).count()
        edge_count = db.query(KnowledgeEdge).count()
        db_ok = True
    except Exception:
        source_count = node_count = edge_count = 0
        db_ok = False
    finally:
        db.close()

    knowledge_base_empty = db_ok and source_count == 0
    if not db_ok:
        status = "degraded"
    elif knowledge_base_empty:
        # A reachable but empty knowledge base means seeding failed (e.g. the
        # seed data wasn't packaged into this deployment) -- surfaced here
        # rather than silently reported as "ok", since this previously broke
        # invisibly inside Docker. See app/knowledge/seed.py::_data_dir.
        status = "degraded"
    else:
        status = "ok"

    notes = []
    if knowledge_base_empty:
        notes.append(
            "Knowledge base is empty (0 sources) but the database is reachable -- seeding likely failed "
            "or the seed data was not packaged into this deployment. Check startup logs and SEED_DATA_DIR."
        )

    return {
        "status": status,
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "ok" if db_ok else "unavailable",
        "llm_provider": get_llm_provider().name,
        "embedding_provider": settings.embedding_provider,
        "notes": notes,
        "knowledge_base": {
            "sources": source_count,
            "graph_nodes": node_count,
            "graph_edges": edge_count,
        },
    }


@app.get("/health/ready")
def readiness():
    """Strict readiness probe: returns 503 if the database is not reachable.
    Intended for orchestrators (Railway, Kubernetes, etc.) to gate traffic
    routing, distinct from the informational /health endpoint above."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    finally:
        db.close()


app.include_router(api_router, prefix=settings.api_prefix)

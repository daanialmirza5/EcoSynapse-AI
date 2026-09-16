from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        return await call_next(request)


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
    logger.info("EcoSynapse AI backend started (llm=%s, embeddings=%s)", get_llm_provider().name, type(get_embedding_provider()).__name__)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Evidence-grounded ecological intelligence and intervention planning API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(MaxBodySizeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
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

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "ok" if db_ok else "unavailable",
        "llm_provider": get_llm_provider().name,
        "embedding_provider": settings.embedding_provider,
        "knowledge_base": {
            "sources": source_count,
            "graph_nodes": node_count,
            "graph_edges": edge_count,
        },
    }


app.include_router(api_router, prefix=settings.api_prefix)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from .config import settings
from .logging import setup_logging, StructlogMiddleware
from .utils.security import BasicAuthMiddleware, RateLimitMiddleware
from .db import init_db
from .routes import projects, ws, index, search, diff, file
import asyncio

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI()
    app.add_middleware(StructlogMiddleware)
    # Security middlewares: rate limiting and optional basic auth
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(BasicAuthMiddleware)
    app.add_middleware(GZipMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Set to your frontend origin
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(projects.router, prefix="/api/projects")
    app.include_router(ws.router)
    app.include_router(index.router)
    app.include_router(search.router)
    app.include_router(diff.router)
    app.include_router(file.router)

    @app.on_event("startup")
    async def on_startup():
        await init_db()
        # TODO: Connect to Redis, Celery, etc.

    @app.on_event("shutdown")
    async def on_shutdown():
        # TODO: Graceful shutdown for DB, Redis, Celery
        pass

    return app

app = create_app()

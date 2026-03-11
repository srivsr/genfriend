from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.config import settings
from app.api.router import api_router
from app.core import init_db, close_redis
from app.core.logging_config import setup_logging
from app.middleware import RequestLoggingMiddleware, RateLimiterMiddleware
from app import models  # noqa: F401 - register models with Base

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    description="AI-powered productivity companion",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Middleware (order matters: last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name, "version": "3.0.0"}


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from app.core.database import engine
    from app.core.redis import get_redis
    from starlette.responses import JSONResponse

    checks = {"database": False, "redis": None}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    if settings.redis_enabled:
        try:
            r = await get_redis()
            if r:
                await r.ping()
                checks["redis"] = True
            else:
                checks["redis"] = False
        except Exception:
            checks["redis"] = False

    all_ok = checks["database"] and (checks["redis"] is None or checks["redis"])
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}", "docs": "/docs"}

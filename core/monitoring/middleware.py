from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time
import logging

from core.monitoring import track_http_request

logger = logging.getLogger(__name__)

def setup_monitoring(app: FastAPI):
    @app.middleware("http")
    async def monitor_requests(request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        method = request.method
        endpoint = request.url.path
        status = response.status_code
        
        track_http_request(method, endpoint, status, duration)
        
        if duration > 1.0:
            logger.warning(f"Slow request: {method} {endpoint} took {duration:.2f}s")
        
        return response
    
    @app.get("/metrics")
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/health")
    async def health():
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        from config import DATABASE_URL
        
        health_status = {
            "status": "healthy",
            "checks": {}
        }
        
        try:
            engine = create_async_engine(
                DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            )
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "ok"
            await engine.dispose()
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
        
        try:
            from config import REDIS_URL
            import redis.asyncio as aioredis
            
            redis_client = aioredis.from_url(REDIS_URL)
            await redis_client.ping()
            health_status["checks"]["redis"] = "ok"
            await redis_client.close()
        except Exception as e:
            health_status["checks"]["redis"] = f"error: {str(e)}"
        
        try:
            from config import OPENAI_API_KEY
            if OPENAI_API_KEY:
                health_status["checks"]["openai"] = "configured"
            else:
                health_status["checks"]["openai"] = "not configured"
        except Exception as e:
            health_status["checks"]["openai"] = f"error: {str(e)}"
        
        return health_status
    
    @app.get("/ready")
    async def ready():
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        from config import DATABASE_URL
        
        try:
            engine = create_async_engine(
                DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            )
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            return {"status": "ready"}
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return Response(
                content={"status": "not ready", "error": str(e)},
                status_code=503
            )
    
    @app.get("/live")
    async def live():
        return {"status": "alive"}
    
    logger.info("Monitoring middleware configured")

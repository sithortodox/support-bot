from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time
from datetime import datetime
import sys

router = APIRouter(tags=["Monitoring"])

@router.get("/metrics")
async def metrics():
    from core.monitoring import update_uptime
    update_uptime()
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/health")
async def health_check():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy import text
    from config import DATABASE_URL, REDIS_URL
    import redis.asyncio as redis
    import os
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime": time.time() - time.time(),
        "components": {}
    }
    
    try:
        engine = create_async_engine(
            DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=False
        )
        
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
        
        await engine.dispose()
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    try:
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        
        health_status["components"]["redis"] = {
            "status": "healthy",
            "type": "redis"
        }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    try:
        from config import OPENAI_API_KEY
        if OPENAI_API_KEY:
            health_status["components"]["openai"] = {
                "status": "configured",
                "has_api_key": True
            }
        else:
            health_status["components"]["openai"] = {
                "status": "not_configured",
                "has_api_key": False
            }
    except Exception as e:
        health_status["components"]["openai"] = {
            "status": "error",
            "error": str(e)
        }
    
    health_status["components"]["python"] = {
        "version": sys.version,
        "implementation": sys.implementation.name
    }
    
    health_status["components"]["system"] = {
        "platform": sys.platform,
        "hostname": os.getenv("HOSTNAME", "unknown")
    }
    
    from sqlalchemy import select, func
    from core.database.models import Ticket, User, UserBlock
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    try:
        engine = create_async_engine(
            DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=False
        )
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with async_session() as session:
            open_tickets = await session.scalar(
                select(func.count(Ticket.id)).where(Ticket.status == "open")
            )
            blocked_users = await session.scalar(
                select(func.count(UserBlock.id)).where(UserBlock.is_active == True)
            )
            
            health_status["metrics"] = {
                "open_tickets": open_tickets or 0,
                "blocked_users": blocked_users or 0
            }
    except Exception as e:
        health_status["metrics"] = {
            "error": str(e)
        }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return health_status

@router.get("/ready")
async def readiness_check():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    from config import DATABASE_URL
    import redis.asyncio as redis
    from config import REDIS_URL
    
    try:
        engine = create_async_engine(
            DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=False
        )
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        
        return {"status": "ready"}
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        }, 503

@router.get("/live")
async def liveness_check():
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

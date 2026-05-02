from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

class AIStatsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float
    avg_response_time: Optional[float]
    faq_usage_rate: float

class SatisfactionStatsResponse(BaseModel):
    total_ratings: int
    positive: int
    negative: int
    satisfaction_rate: Optional[float]

class CategoryDistributionResponse(BaseModel):
    categories: dict
    total: int

class HourlyActivityResponse(BaseModel):
    hour: int
    count: int

class AggregationResponse(BaseModel):
    date: datetime
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    total_messages: int
    ai_messages: int
    admin_messages: int
    total_tokens: int
    estimated_cost: float
    avg_response_time: Optional[float]
    satisfaction_rate: Optional[float]
    faq_used: int

@router.get("/ai", response_model=AIStatsResponse)
async def get_ai_analytics(
    project_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=720)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        stats = await db.get_ai_stats(project_id, hours)
        return AIStatsResponse(**stats)

@router.get("/satisfaction", response_model=SatisfactionStatsResponse)
async def get_satisfaction_analytics(
    project_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=720)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        stats = await db.get_satisfaction_stats(project_id, hours)
        return SatisfactionStatsResponse(**stats)

@router.get("/categories", response_model=CategoryDistributionResponse)
async def get_category_distribution(
    project_id: Optional[int] = None,
    hours: int = Query(168, ge=1, le=720)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        stats = await db.get_category_distribution(project_id, hours)
        return CategoryDistributionResponse(**stats)

@router.get("/sentiment")
async def get_sentiment_distribution(
    project_id: Optional[int] = None,
    hours: int = Query(168, ge=1, le=720)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        stats = await db.get_sentiment_distribution(project_id, hours)
        return stats

@router.get("/activity", response_model=List[HourlyActivityResponse])
async def get_hourly_activity(
    project_id: Optional[int] = None,
    hours: int = Query(168, ge=1, le=720)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        stats = await db.get_hourly_activity(project_id, hours)
        return [HourlyActivityResponse(**s) for s in stats]

@router.get("/history", response_model=List[AggregationResponse])
async def get_aggregation_history(
    project_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        history = await db.get_aggregation_history(project_id, days)
        return [
            AggregationResponse(
                date=agg.date,
                total_tickets=agg.total_tickets,
                open_tickets=agg.open_tickets,
                closed_tickets=agg.closed_tickets,
                total_messages=agg.total_messages,
                ai_messages=agg.ai_messages,
                admin_messages=agg.admin_messages,
                total_tokens=agg.total_tokens,
                estimated_cost=agg.estimated_cost,
                avg_response_time=agg.avg_response_time,
                satisfaction_rate=agg.satisfaction_rate,
                faq_used=agg.faq_used
            )
            for agg in history
        ]

@router.get("/export/tickets")
async def export_tickets(
    project_id: Optional[int] = None,
    hours: int = Query(720, ge=1, le=2160)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        csv_data = await db.export_tickets_csv(project_id, hours)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tickets_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            }
        )

@router.get("/dashboard")
async def get_dashboard_data(
    project_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=720)
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        
        ai_stats = await db.get_ai_stats(project_id, hours)
        satisfaction = await db.get_satisfaction_stats(project_id, hours)
        categories = await db.get_category_distribution(project_id, hours)
        sentiment = await db.get_sentiment_distribution(project_id, hours)
        activity = await db.get_hourly_activity(project_id, hours)
        ticket_stats = await db.get_ticket_stats(project_id, hours)
        
        return {
            "period_hours": hours,
            "ai": ai_stats,
            "satisfaction": satisfaction,
            "categories": categories,
            "sentiment": sentiment,
            "activity": activity,
            "tickets": ticket_stats
        }

@router.post("/aggregate")
async def trigger_aggregation(
    project_id: Optional[int] = None,
    date: Optional[str] = None
):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    from datetime import datetime
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        
        target_date = datetime.utcnow()
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        agg = await db.create_or_update_aggregation(target_date, project_id)
        
        return {
            "status": "success",
            "aggregation_id": agg.id,
            "date": agg.date.isoformat()
        }

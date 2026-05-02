from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Support Bot API", version="1.0.0")

class MessageCreate(BaseModel):
    ticket_id: int
    content: str
    sender_type: str = "admin"

class TicketResponse(BaseModel):
    id: int
    status: str
    priority: str
    created_at: str

class StatsResponse(BaseModel):
    total_users: int
    total_tickets: int
    open_tickets: int

@app.get("/")
async def root():
    return {"status": "ok", "service": "Support Bot API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    from core.config import BOT_TOKEN, WEBHOOK_SECRET
    from aiogram.types import Update
    
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    try:
        data = await request.json()
        update = Update(**data)
        
        from main import dp, bot
        
        await dp.feed_update(bot, update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/admin/tickets", response_model=List[TicketResponse])
async def get_tickets(status: Optional[str] = None, limit: int = 50):
    from core.database import Database
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.database import Base
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        tickets = await db.get_open_tickets(limit=limit)
        
        return [
            TicketResponse(
                id=t.id,
                status=t.status,
                priority=t.priority,
                created_at=t.created_at.isoformat()
            )
            for t in tickets
        ]

@app.post("/admin/message")
async def send_message(message: MessageCreate):
    from core.database import Database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL, BOT_TOKEN
    from aiogram import Bot
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        db = Database(session)
        
        ticket = await db.get_ticket(message.ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        await db.create_message(
            ticket_id=message.ticket_id,
            sender_type=message.sender_type,
            content=message.content
        )
        
        try:
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                chat_id=ticket.user.telegram_id,
                text=f"📨 Ответ: {message.content}"
            )
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
        
        return {"status": "ok", "message": "Message sent"}

@app.get("/admin/stats", response_model=StatsResponse)
async def get_stats():
    from sqlalchemy import select, func
    from core.database.models import Ticket, User
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from core.config import DATABASE_URL
    
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        total_tickets = await session.scalar(select(func.count(Ticket.id)))
        open_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == "open")
        )
        
        return StatsResponse(
            total_users=total_users or 0,
            total_tickets=total_tickets or 0,
            open_tickets=open_tickets or 0
        )

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, BigInteger, Boolean, ForeignKey, Text, func, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
import enum

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")
    language: Mapped[str] = mapped_column(String(10), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    total_tickets: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    context: Mapped[Optional["UserContext"]] = relationship(back_populates="user", uselist=False)

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bot_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(50), default="normal")
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    assigned_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="tickets", foreign_keys=[user_id])
    project: Mapped[Optional["Project"]] = relationship(back_populates="tickets")
    messages: Mapped[List["Message"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    sender_type: Mapped[str] = mapped_column(String(50))
    sender_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    ticket: Mapped["Ticket"] = relationship(back_populates="messages")

class AILog(Base):
    __tablename__ = "ai_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    prompt_tokens: Mapped[int] = mapped_column()
    completion_tokens: Mapped[int] = mapped_column()
    model: Mapped[str] = mapped_column(String(100))
    response_time: Mapped[Optional[float]] = mapped_column(nullable=True)
    used_faq: Mapped[bool] = mapped_column(Boolean, default=False)
    faq_id: Mapped[Optional[int]] = mapped_column(ForeignKey("faqs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class FAQ(Base):
    __tablename__ = "faqs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

class UserContext(Base):
    __tablename__ = "user_contexts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    recent_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    last_interaction: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    avg_sentiment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="context")

class SentimentLog(Base):
    __tablename__ = "sentiment_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    sentiment: Mapped[str] = mapped_column(String(50))
    score: Mapped[float] = mapped_column(Float)
    emotions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

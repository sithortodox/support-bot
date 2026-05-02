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
    
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="user", foreign_keys="Ticket.user_id", cascade="all, delete-orphan")
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
    first_response_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    response_time_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    rating: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    has_attachment: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    ticket: Mapped["Ticket"] = relationship(back_populates="messages")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")

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

class Attachment(Base):
    __tablename__ = "attachments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), index=True)
    file_type: Mapped[str] = mapped_column(String(50))
    file_id: Mapped[str] = mapped_column(String(255))
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    message: Mapped["Message"] = relationship(back_populates="attachments")

class ResponseTemplate(Base):
    __tablename__ = "response_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

class RatingLog(Base):
    __tablename__ = "rating_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    rating: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class TicketCategory(Base):
    __tablename__ = "ticket_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class UserBlock(Base):
    __tablename__ = "user_blocks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    blocked_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    block_type: Mapped[str] = mapped_column(String(50), default="temporary")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    unblocked_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    unblocked_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class RateLimitLog(Base):
    __tablename__ = "rate_limit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50))
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    first_attempt: Mapped[datetime] = mapped_column(server_default=func.now())
    last_attempt: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)

class SpamFilter(Base):
    __tablename__ = "spam_filters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    pattern: Mapped[str] = mapped_column(String(255), unique=True)
    filter_type: Mapped[str] = mapped_column(String(50), default="keyword")
    action: Mapped[str] = mapped_column(String(50), default="warn")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class SecuritySettings(Base):
    __tablename__ = "security_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    setting_key: Mapped[str] = mapped_column(String(100), unique=True)
    setting_value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

class AnalyticsAggregation(Base):
    __tablename__ = "analytics_aggregations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    
    total_tickets: Mapped[int] = mapped_column(Integer, default=0)
    open_tickets: Mapped[int] = mapped_column(Integer, default=0)
    closed_tickets: Mapped[int] = mapped_column(Integer, default=0)
    
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    ai_messages: Mapped[int] = mapped_column(Integer, default=0)
    admin_messages: Mapped[int] = mapped_column(Integer, default=0)
    
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    avg_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    positive_ratings: Mapped[int] = mapped_column(Integer, default=0)
    negative_ratings: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    faq_used: Mapped[int] = mapped_column(Integer, default=0)
    
    users_blocked: Mapped[int] = mapped_column(Integer, default=0)
    spam_detected: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

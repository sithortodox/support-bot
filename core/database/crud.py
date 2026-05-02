from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Base, User, Project, Ticket, Message, AILog, FAQ, UserContext, SentimentLog

class Database:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_tables(self):
        from sqlalchemy.ext.asyncio import create_async_engine
        from ..config import DATABASE_URL
        
        engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        
        return user
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        bot_token: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Project:
        project = Project(
            name=name,
            description=description,
            bot_token=bot_token,
            system_prompt=system_prompt
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project
    
    async def get_project(self, project_id: int) -> Optional[Project]:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_projects(self) -> List[Project]:
        result = await self.session.execute(
            select(Project).where(Project.is_active == True)
        )
        return result.scalars().all()
    
    async def create_ticket(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        priority: str = "normal"
    ) -> Ticket:
        ticket = Ticket(
            user_id=user_id,
            project_id=project_id,
            priority=priority,
            status="open"
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket
    
    async def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_tickets(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Ticket]:
        query = select(Ticket).where(Ticket.user_id == user_id)
        if status:
            query = query.where(Ticket.status == status)
        query = query.order_by(Ticket.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_open_tickets(self, limit: int = 50) -> List[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.status.in_(["open", "human_handled"]))
            .order_by(Ticket.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_ticket_status(
        self,
        ticket_id: int,
        status: str,
        assigned_admin_id: Optional[int] = None
    ) -> Optional[Ticket]:
        ticket = await self.get_ticket(ticket_id)
        if ticket:
            ticket.status = status
            if assigned_admin_id:
                ticket.assigned_admin_id = assigned_admin_id
            if status == "closed":
                ticket.closed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(ticket)
        return ticket
    
    async def create_message(
        self,
        ticket_id: int,
        sender_type: str,
        content: str,
        sender_id: Optional[int] = None
    ) -> Message:
        message = Message(
            ticket_id=ticket_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_ticket_messages(
        self,
        ticket_id: int,
        limit: int = 20
    ) -> List[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.ticket_id == ticket_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_ai_log(
        self,
        ticket_id: int,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        response_time: Optional[float] = None
    ) -> AILog:
        log = AILog(
            ticket_id=ticket_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
            response_time=response_time
        )
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_admin_users(self) -> List[User]:
        result = await self.session.execute(
            select(User).where(User.role.in_(["admin", "moderator"]))
        )
        return result.scalars().all()
    
    async def set_user_role(self, telegram_id: int, role: str) -> Optional[User]:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            user.role = role
            await self.session.commit()
            await self.session.refresh(user)
        return user
    
    async def get_or_create_user_context(self, user_id: int) -> UserContext:
        result = await self.session.execute(
            select(UserContext).where(UserContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()
        
        if not context:
            context = UserContext(user_id=user_id)
            self.session.add(context)
            await self.session.commit()
            await self.session.refresh(context)
        
        return context
    
    async def update_user_context(
        self,
        user_id: int,
        topic: Optional[str] = None,
        language: Optional[str] = None,
        sentiment_score: Optional[float] = None
    ) -> UserContext:
        context = await self.get_or_create_user_context(user_id)
        
        if topic:
            existing_topics = context.recent_topics or ""
            topics_list = existing_topics.split("|") if existing_topics else []
            topics_list = [t for t in topics_list if t][:9]
            topics_list.insert(0, topic)
            context.recent_topics = "|".join(topics_list)
        
        if language:
            context.preferred_language = language
        
        if sentiment_score is not None:
            total = context.total_messages or 0
            current_avg = context.avg_sentiment or 0.5
            context.avg_sentiment = (current_avg * total + sentiment_score) / (total + 1)
        
        context.total_messages = (context.total_messages or 0) + 1
        context.last_interaction = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(context)
        return context
    
    async def create_faq(
        self,
        question: str,
        answer: str,
        project_id: Optional[int] = None,
        keywords: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "ru"
    ) -> FAQ:
        faq = FAQ(
            project_id=project_id,
            question=question,
            answer=answer,
            keywords=keywords,
            category=category,
            language=language
        )
        self.session.add(faq)
        await self.session.commit()
        await self.session.refresh(faq)
        return faq
    
    async def get_faq(self, faq_id: int) -> Optional[FAQ]:
        result = await self.session.execute(
            select(FAQ).where(FAQ.id == faq_id)
        )
        return result.scalar_one_or_none()
    
    async def search_faq(
        self,
        query: str,
        project_id: Optional[int] = None,
        language: Optional[str] = None,
        limit: int = 5
    ) -> List[FAQ]:
        query_lower = query.lower()
        
        sql_query = select(FAQ).where(
            FAQ.is_active == True,
            or_(
                FAQ.question.ilike(f"%{query_lower}%"),
                FAQ.keywords.ilike(f"%{query_lower}%")
            )
        )
        
        if project_id:
            sql_query = sql_query.where(
                or_(FAQ.project_id == project_id, FAQ.project_id == None)
            )
        
        if language:
            sql_query = sql_query.where(FAQ.language == language)
        
        sql_query = sql_query.order_by(desc(FAQ.priority)).limit(limit)
        
        result = await self.session.execute(sql_query)
        return result.scalars().all()
    
    async def get_all_faqs(
        self,
        project_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[FAQ]:
        query = select(FAQ).where(FAQ.is_active == True)
        
        if project_id:
            query = query.where(FAQ.project_id == project_id)
        
        if category:
            query = query.where(FAQ.category == category)
        
        query = query.order_by(desc(FAQ.priority), desc(FAQ.use_count)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def increment_faq_use(self, faq_id: int) -> None:
        faq = await self.get_faq(faq_id)
        if faq:
            faq.use_count = (faq.use_count or 0) + 1
            await self.session.commit()
    
    async def create_sentiment_log(
        self,
        ticket_id: int,
        message_id: int,
        sentiment: str,
        score: float,
        emotions: Optional[str] = None
    ) -> SentimentLog:
        log = SentimentLog(
            ticket_id=ticket_id,
            message_id=message_id,
            sentiment=sentiment,
            score=score,
            emotions=emotions
        )
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_ticket_sentiment_history(self, ticket_id: int) -> List[SentimentLog]:
        result = await self.session.execute(
            select(SentimentLog)
            .where(SentimentLog.ticket_id == ticket_id)
            .order_by(SentimentLog.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_user_ticket_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_ticket_sentiment(
        self,
        ticket_id: int,
        sentiment: str,
        score: float
    ) -> Optional[Ticket]:
        ticket = await self.get_ticket(ticket_id)
        if ticket:
            ticket.sentiment = sentiment
            ticket.sentiment_score = score
            await self.session.commit()
            await self.session.refresh(ticket)
        return ticket
    
    async def update_ticket_language(
        self,
        ticket_id: int,
        language: str
    ) -> Optional[Ticket]:
        ticket = await self.get_ticket(ticket_id)
        if ticket:
            ticket.language = language
            await self.session.commit()
            await self.session.refresh(ticket)
        return ticket
    
    async def update_ticket_category(
        self,
        ticket_id: int,
        category: str
    ) -> Optional[Ticket]:
        ticket = await self.get_ticket(ticket_id)
        if ticket:
            ticket.category = category
            await self.session.commit()
            await self.session.refresh(ticket)
        return ticket
    
    async def create_ai_log_with_faq(
        self,
        ticket_id: int,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        used_faq: bool = False,
        faq_id: Optional[int] = None,
        response_time: Optional[float] = None
    ) -> AILog:
        log = AILog(
            ticket_id=ticket_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
            used_faq=used_faq,
            faq_id=faq_id,
            response_time=response_time
        )
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_faq_categories(
        self,
        project_id: Optional[int] = None
    ) -> List[str]:
        query = select(FAQ.category).where(
            FAQ.is_active == True,
            FAQ.category != None
        )
        
        if project_id:
            query = query.where(
                or_(FAQ.project_id == project_id, FAQ.project_id == None)
            )
        
        query = query.distinct()
        
        result = await self.session.execute(query)
        return [r for r in result.scalars().all() if r]

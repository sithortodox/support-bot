from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from .models import (
    Base, User, Project, Ticket, Message, AILog,
    FAQ, UserContext, SentimentLog, Attachment,
    ResponseTemplate, RatingLog, TicketCategory,
    UserBlock, AuditLog, RateLimitLog, SpamFilter, SecuritySettings
)

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
    
    async def create_attachment(
        self,
        message_id: int,
        file_type: str,
        file_id: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> Attachment:
        attachment = Attachment(
            message_id=message_id,
            file_type=file_type,
            file_id=file_id,
            file_name=file_name,
            file_size=file_size
        )
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment
    
    async def get_message_attachments(
        self,
        message_id: int
    ) -> List[Attachment]:
        result = await self.session.execute(
            select(Attachment)
            .where(Attachment.message_id == message_id)
        )
        return result.scalars().all()
    
    async def create_response_template(
        self,
        name: str,
        content: str,
        project_id: Optional[int] = None,
        category: Optional[str] = None,
        language: str = "ru",
        created_by: Optional[int] = None
    ) -> ResponseTemplate:
        template = ResponseTemplate(
            project_id=project_id,
            name=name,
            content=content,
            category=category,
            language=language,
            created_by=created_by
        )
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template
    
    async def get_response_templates(
        self,
        project_id: Optional[int] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20
    ) -> List[ResponseTemplate]:
        query = select(ResponseTemplate).where(ResponseTemplate.is_active == True)
        
        if project_id:
            query = query.where(
                or_(ResponseTemplate.project_id == project_id, ResponseTemplate.project_id == None)
            )
        
        if category:
            query = query.where(ResponseTemplate.category == category)
        
        if language:
            query = query.where(ResponseTemplate.language == language)
        
        query = query.order_by(desc(ResponseTemplate.use_count)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def increment_template_use(self, template_id: int) -> None:
        result = await self.session.execute(
            select(ResponseTemplate).where(ResponseTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if template:
            template.use_count = (template.use_count or 0) + 1
            await self.session.commit()
    
    async def rate_message(
        self,
        message_id: int,
        user_id: int,
        ticket_id: int,
        rating: str
    ) -> RatingLog:
        log = RatingLog(
            message_id=message_id,
            user_id=user_id,
            ticket_id=ticket_id,
            rating=rating
        )
        self.session.add(log)
        
        result = await self.session.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()
        if message:
            message.rating = rating
        
        await self.session.commit()
        return log
    
    async def get_message_rating(self, message_id: int) -> Optional[str]:
        result = await self.session.execute(
            select(Message.rating).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()
    
    async def update_first_response_time(
        self,
        ticket_id: int
    ) -> Optional[Ticket]:
        ticket = await self.get_ticket(ticket_id)
        if ticket and not ticket.first_response_at:
            from datetime import datetime
            ticket.first_response_at = datetime.utcnow()
            ticket.response_time_minutes = (
                ticket.first_response_at - ticket.created_at
            ).total_seconds() / 60
            await self.session.commit()
            await self.session.refresh(ticket)
        return ticket
    
    async def get_average_response_time(
        self,
        project_id: Optional[int] = None,
        hours: int = 24
    ) -> Optional[float]:
        from datetime import datetime, timedelta
        from sqlalchemy import func as sql_func
        
        query = select(
            sql_func.avg(Ticket.response_time_minutes)
        ).where(
            Ticket.response_time_minutes != None,
            Ticket.first_response_at >= datetime.utcnow() - timedelta(hours=hours)
        )
        
        if project_id:
            query = query.where(Ticket.project_id == project_id)
        
        result = await self.session.scalar(query)
        return result
    
    async def create_ticket_category(
        self,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        priority: int = 0
    ) -> TicketCategory:
        category = TicketCategory(
            name=name,
            description=description,
            emoji=emoji,
            priority=priority
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def get_ticket_categories(self) -> List[TicketCategory]:
        result = await self.session.execute(
            select(TicketCategory)
            .where(TicketCategory.is_active == True)
            .order_by(TicketCategory.priority.desc())
        )
        return result.scalars().all()
    
    async def get_ticket_stats(
        self,
        project_id: Optional[int] = None,
        hours: int = 24
    ) -> dict:
        from datetime import datetime, timedelta
        from sqlalchemy import func as sql_func
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        base_query = select(Ticket).where(Ticket.created_at >= since)
        
        if project_id:
            base_query = base_query.where(Ticket.project_id == project_id)
        
        total = await self.session.scalar(
            select(sql_func.count()).select_from(base_query.subquery())
        )
        
        open_count = await self.session.scalar(
            select(sql_func.count()).select_from(
                base_query.where(Ticket.status == "open").subquery()
            )
        )
        
        closed_count = await self.session.scalar(
            select(sql_func.count()).select_from(
                base_query.where(Ticket.status == "closed").subquery()
            )
        )
        
        avg_response_time = await self.get_average_response_time(project_id, hours)
        
        positive_ratings = await self.session.scalar(
            select(sql_func.count(RatingLog.id)).where(
                RatingLog.created_at >= since,
                RatingLog.rating == "positive"
            )
        )
        
        negative_ratings = await self.session.scalar(
            select(sql_func.count(RatingLog.id)).where(
                RatingLog.created_at >= since,
                RatingLog.rating == "negative"
            )
        )
        
        return {
            "total_tickets": total or 0,
            "open_tickets": open_count or 0,
            "closed_tickets": closed_count or 0,
            "avg_response_time_minutes": avg_response_time,
            "positive_ratings": positive_ratings or 0,
            "negative_ratings": negative_ratings or 0,
            "satisfaction_rate": (
                (positive_ratings or 0) / max((positive_ratings or 0) + (negative_ratings or 0), 1) * 100
            )
        }
    
    async def block_user(
        self,
        user_id: int,
        blocked_by: int,
        reason: Optional[str] = None,
        block_type: str = "temporary",
        duration_hours: Optional[int] = None
    ) -> UserBlock:
        from datetime import datetime, timedelta
        
        expires_at = None
        if duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        block = UserBlock(
            user_id=user_id,
            blocked_by=blocked_by,
            reason=reason,
            block_type=block_type,
            expires_at=expires_at
        )
        self.session.add(block)
        
        user = await self.get_user_by_telegram_id(user_id)
        if user:
            user.is_active = False
        
        await self.session.commit()
        await self.session.refresh(block)
        return block
    
    async def unblock_user(
        self,
        user_id: int,
        unblocked_by: int
    ) -> Optional[UserBlock]:
        result = await self.session.execute(
            select(UserBlock).where(
                UserBlock.user_id == user_id,
                UserBlock.is_active == True
            ).order_by(UserBlock.created_at.desc())
        )
        block = result.scalar_one_or_none()
        
        if block:
            block.is_active = False
            block.unblocked_at = datetime.utcnow()
            block.unblocked_by = unblocked_by
            
            user = await self.get_user_by_telegram_id(user_id)
            if user:
                user.is_active = True
            
            await self.session.commit()
            await self.session.refresh(block)
        
        return block
    
    async def is_user_blocked(self, user_id: int) -> tuple[bool, Optional[str]]:
        from datetime import datetime
        
        result = await self.session.execute(
            select(UserBlock).where(
                UserBlock.user_id == user_id,
                UserBlock.is_active == True,
                or_(
                    UserBlock.expires_at == None,
                    UserBlock.expires_at > datetime.utcnow()
                )
            ).order_by(UserBlock.created_at.desc())
        )
        block = result.scalar_one_or_none()
        
        if block:
            return True, block.reason
        return False, None
    
    async def get_user_blocks(
        self,
        user_id: Optional[int] = None,
        active_only: bool = True,
        limit: int = 50
    ) -> List[UserBlock]:
        query = select(UserBlock)
        
        if user_id:
            query = query.where(UserBlock.user_id == user_id)
        
        if active_only:
            query = query.where(UserBlock.is_active == True)
        
        query = query.order_by(UserBlock.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_audit_log(
        self,
        admin_id: int,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_audit_logs(
        self,
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        from datetime import datetime, timedelta
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(AuditLog).where(AuditLog.created_at >= since)
        
        if admin_id:
            query = query.where(AuditLog.admin_id == admin_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def check_rate_limit(
        self,
        user_id: int,
        action_type: str,
        max_attempts: int = 10,
        window_minutes: int = 60
    ) -> tuple[bool, int]:
        from datetime import datetime, timedelta
        
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        result = await self.session.execute(
            select(RateLimitLog).where(
                RateLimitLog.user_id == user_id,
                RateLimitLog.action_type == action_type,
                RateLimitLog.first_attempt >= window_start
            )
        )
        log = result.scalar_one_or_none()
        
        if not log:
            log = RateLimitLog(
                user_id=user_id,
                action_type=action_type,
                attempt_count=1
            )
            self.session.add(log)
            await self.session.commit()
            return True, max_attempts - 1
        
        if log.attempt_count >= max_attempts:
            log.is_blocked = True
            log.blocked_until = datetime.utcnow() + timedelta(minutes=window_minutes)
            await self.session.commit()
            return False, 0
        
        log.attempt_count += 1
        await self.session.commit()
        return True, max_attempts - log.attempt_count
    
    async def get_rate_limit_status(
        self,
        user_id: int,
        action_type: str
    ) -> Optional[RateLimitLog]:
        result = await self.session.execute(
            select(RateLimitLog).where(
                RateLimitLog.user_id == user_id,
                RateLimitLog.action_type == action_type
            ).order_by(RateLimitLog.last_attempt.desc())
        )
        return result.scalar_one_or_none()
    
    async def reset_rate_limit(
        self,
        user_id: int,
        action_type: str
    ) -> None:
        result = await self.session.execute(
            select(RateLimitLog).where(
                RateLimitLog.user_id == user_id,
                RateLimitLog.action_type == action_type
            )
        )
        logs = result.scalars().all()
        
        for log in logs:
            log.is_blocked = False
            log.blocked_until = None
            log.attempt_count = 0
        
        await self.session.commit()
    
    async def create_spam_filter(
        self,
        pattern: str,
        filter_type: str = "keyword",
        action: str = "warn",
        created_by: Optional[int] = None
    ) -> SpamFilter:
        spam_filter = SpamFilter(
            pattern=pattern,
            filter_type=filter_type,
            action=action,
            created_by=created_by
        )
        self.session.add(spam_filter)
        await self.session.commit()
        await self.session.refresh(spam_filter)
        return spam_filter
    
    async def check_spam(self, message: str) -> Optional[SpamFilter]:
        message_lower = message.lower()
        
        result = await self.session.execute(
            select(SpamFilter).where(
                SpamFilter.is_active == True,
                SpamFilter.filter_type == "keyword"
            )
        )
        filters = result.scalars().all()
        
        for spam_filter in filters:
            if spam_filter.pattern.lower() in message_lower:
                return spam_filter
        
        return None
    
    async def get_spam_filters(
        self,
        filter_type: Optional[str] = None,
        limit: int = 50
    ) -> List[SpamFilter]:
        query = select(SpamFilter).where(SpamFilter.is_active == True)
        
        if filter_type:
            query = query.where(SpamFilter.filter_type == filter_type)
        
        query = query.order_by(SpamFilter.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def delete_spam_filter(self, filter_id: int) -> bool:
        result = await self.session.execute(
            select(SpamFilter).where(SpamFilter.id == filter_id)
        )
        spam_filter = result.scalar_one_or_none()
        
        if spam_filter:
            spam_filter.is_active = False
            await self.session.commit()
            return True
        return False
    
    async def get_security_setting(
        self,
        key: str,
        default: str = ""
    ) -> str:
        result = await self.session.execute(
            select(SecuritySettings).where(SecuritySettings.setting_key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.setting_value if setting else default
    
    async def set_security_setting(
        self,
        key: str,
        value: str,
        updated_by: Optional[int] = None,
        description: Optional[str] = None
    ) -> SecuritySettings:
        result = await self.session.execute(
            select(SecuritySettings).where(SecuritySettings.setting_key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.setting_value = value
            setting.updated_by = updated_by
            if description:
                setting.description = description
        else:
            setting = SecuritySettings(
                setting_key=key,
                setting_value=value,
                description=description,
                updated_by=updated_by
            )
            self.session.add(setting)
        
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

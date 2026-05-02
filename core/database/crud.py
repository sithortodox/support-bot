from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Base, User, Project, Ticket, Message, AILog

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

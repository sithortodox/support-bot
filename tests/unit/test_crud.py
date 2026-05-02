import pytest
from core.database.crud import Database
from core.database.models import User, Ticket, Message, FAQ

class TestUserCRUD:
    @pytest.mark.asyncio
    async def test_get_or_create_user(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        
        assert user is not None
        assert user.telegram_id == sample_user_data["telegram_id"]
        assert user.username == sample_user_data["username"]
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self, db: Database, sample_user_data: dict):
        user1 = await db.get_or_create_user(**sample_user_data)
        user2 = await db.get_or_create_user(**sample_user_data)
        
        assert user1.id == user2.id
    
    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id(self, db: Database, sample_user_data: dict):
        await db.get_or_create_user(**sample_user_data)
        
        user = await db.get_user_by_telegram_id(sample_user_data["telegram_id"])
        
        assert user is not None
        assert user.telegram_id == sample_user_data["telegram_id"]
    
    @pytest.mark.asyncio
    async def test_set_user_role(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        
        updated_user = await db.set_user_role(user.telegram_id, "admin")
        
        assert updated_user.role == "admin"

class TestTicketCRUD:
    @pytest.mark.asyncio
    async def test_create_ticket(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        
        ticket = await db.create_ticket(user_id=user.id)
        
        assert ticket is not None
        assert ticket.user_id == user.id
        assert ticket.status == "open"
        assert ticket.priority == "normal"
    
    @pytest.mark.asyncio
    async def test_get_ticket(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        retrieved = await db.get_ticket(ticket.id)
        
        assert retrieved is not None
        assert retrieved.id == ticket.id
    
    @pytest.mark.asyncio
    async def test_update_ticket_status(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        updated = await db.update_ticket_status(ticket.id, "closed")
        
        assert updated.status == "closed"
        assert updated.closed_at is not None

class TestMessageCRUD:
    @pytest.mark.asyncio
    async def test_create_message(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        message = await db.create_message(
            ticket_id=ticket.id,
            sender_type="user",
            sender_id=user.telegram_id,
            content="Test message"
        )
        
        assert message is not None
        assert message.ticket_id == ticket.id
        assert message.sender_type == "user"
        assert message.content == "Test message"
    
    @pytest.mark.asyncio
    async def test_get_ticket_messages(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        await db.create_message(
            ticket_id=ticket.id,
            sender_type="user",
            content="Message 1"
        )
        await db.create_message(
            ticket_id=ticket.id,
            sender_type="ai",
            content="Message 2"
        )
        
        messages = await db.get_ticket_messages(ticket.id)
        
        assert len(messages) == 2

class TestFAQCRUD:
    @pytest.mark.asyncio
    async def test_create_faq(self, db: Database, sample_faq_data: dict):
        faq = await db.create_faq(**sample_faq_data)
        
        assert faq is not None
        assert faq.question == sample_faq_data["question"]
        assert faq.answer == sample_faq_data["answer"]
    
    @pytest.mark.asyncio
    async def test_search_faq(self, db: Database, sample_faq_data: dict):
        await db.create_faq(**sample_faq_data)
        
        results = await db.search_faq("password reset")
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_increment_faq_use(self, db: Database, sample_faq_data: dict):
        faq = await db.create_faq(**sample_faq_data)
        initial_count = faq.use_count
        
        await db.increment_faq_use(faq.id)
        
        from sqlalchemy import select
        result = await db.session.execute(select(FAQ).where(FAQ.id == faq.id))
        updated_faq = result.scalar_one()
        
        assert updated_faq.use_count == initial_count + 1

class TestSecurityCRUD:
    @pytest.mark.asyncio
    async def test_block_user(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        
        block = await db.block_user(
            user_id=user.telegram_id,
            blocked_by=999,
            reason="Test block",
            duration_hours=24
        )
        
        assert block is not None
        assert block.user_id == user.telegram_id
        assert block.reason == "Test block"
        assert block.is_active == True
    
    @pytest.mark.asyncio
    async def test_is_user_blocked(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        
        is_blocked, reason = await db.is_user_blocked(user.telegram_id)
        assert is_blocked == False
        
        await db.block_user(
            user_id=user.telegram_id,
            blocked_by=999,
            reason="Test block"
        )
        
        is_blocked, reason = await db.is_user_blocked(user.telegram_id)
        assert is_blocked == True
        assert reason == "Test block"
    
    @pytest.mark.asyncio
    async def test_check_rate_limit(self, db: Database, sample_user_data: dict):
        user = await db.get_or_create_user(**sample_user_data)
        
        allowed, remaining = await db.check_rate_limit(
            user_id=user.telegram_id,
            action_type="message",
            max_attempts=10,
            window_minutes=60
        )
        
        assert allowed == True
        assert remaining == 9

class TestAnalyticsCRUD:
    @pytest.mark.asyncio
    async def test_get_ai_stats(self, db: Database):
        stats = await db.get_ai_stats(hours=24)
        
        assert "total_requests" in stats
        assert "total_tokens" in stats
        assert "estimated_cost" in stats
    
    @pytest.mark.asyncio
    async def test_get_satisfaction_stats(self, db: Database):
        stats = await db.get_satisfaction_stats(hours=24)
        
        assert "total_ratings" in stats
        assert "satisfaction_rate" in stats
    
    @pytest.mark.asyncio
    async def test_get_category_distribution(self, db: Database):
        distribution = await db.get_category_distribution(hours=168)
        
        assert "categories" in distribution
        assert "total" in distribution

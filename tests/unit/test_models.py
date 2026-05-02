import pytest
from datetime import datetime
from core.database.models import (
    User, Project, Ticket, Message, AILog,
    FAQ, UserContext, SentimentLog, Attachment,
    ResponseTemplate, RatingLog, TicketCategory,
    UserBlock, AuditLog, RateLimitLog, SpamFilter,
    SecuritySettings, AnalyticsAggregation
)

class TestUserModel:
    def test_user_creation(self):
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == "user"
        assert user.language == "ru"
        assert user.is_active == True
        assert user.total_tickets == 0
    
    def test_user_default_values(self):
        user = User(telegram_id=123456789)
        
        assert user.role == "user"
        assert user.language == "ru"
        assert user.is_active == True
        assert user.total_tickets == 0

class TestTicketModel:
    def test_ticket_creation(self):
        ticket = Ticket(
            user_id=1,
            status="open",
            priority="normal"
        )
        
        assert ticket.status == "open"
        assert ticket.priority == "normal"
        assert ticket.sentiment is None
        assert ticket.sentiment_score is None
        assert ticket.category is None
        assert ticket.language is None
    
    def test_ticket_with_sentiment(self):
        ticket = Ticket(
            user_id=1,
            sentiment="frustrated",
            sentiment_score=0.3,
            category="technical"
        )
        
        assert ticket.sentiment == "frustrated"
        assert ticket.sentiment_score == 0.3
        assert ticket.category == "technical"

class TestMessageModel:
    def test_message_creation(self):
        message = Message(
            ticket_id=1,
            sender_type="user",
            sender_id=123456789,
            content="Test message"
        )
        
        assert message.ticket_id == 1
        assert message.sender_type == "user"
        assert message.sender_id == 123456789
        assert message.content == "Test message"
        assert message.rating is None
        assert message.has_attachment == False

class TestFAQModel:
    def test_faq_creation(self):
        faq = FAQ(
            question="How to reset password?",
            answer="Go to Settings > Security",
            keywords="password, reset",
            category="account",
            language="en"
        )
        
        assert faq.question == "How to reset password?"
        assert faq.answer == "Go to Settings > Security"
        assert faq.keywords == "password, reset"
        assert faq.category == "account"
        assert faq.language == "en"
        assert faq.priority == 0
        assert faq.use_count == 0
        assert faq.is_active == True

class TestUserBlockModel:
    def test_user_block_creation(self):
        block = UserBlock(
            user_id=1,
            blocked_by=2,
            reason="Spam",
            block_type="temporary"
        )
        
        assert block.user_id == 1
        assert block.blocked_by == 2
        assert block.reason == "Spam"
        assert block.block_type == "temporary"
        assert block.is_active == True

class TestAuditLogModel:
    def test_audit_log_creation(self):
        log = AuditLog(
            admin_id=1,
            action="block_user",
            target_type="user",
            target_id=123456789,
            details="Blocked for spam"
        )
        
        assert log.admin_id == 1
        assert log.action == "block_user"
        assert log.target_type == "user"
        assert log.target_id == 123456789
        assert log.details == "Blocked for spam"

class TestAnalyticsAggregationModel:
    def test_aggregation_creation(self):
        agg = AnalyticsAggregation(
            date=datetime.utcnow(),
            total_tickets=100,
            total_messages=500,
            total_tokens=10000,
            estimated_cost=1.5
        )
        
        assert agg.total_tickets == 100
        assert agg.total_messages == 500
        assert agg.total_tokens == 10000
        assert agg.estimated_cost == 1.5
        assert agg.open_tickets == 0
        assert agg.closed_tickets == 0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.router.message_router import MessageRouter
from core.ai.openai_client import OpenAIClient, SentimentResult

class TestMessageRouter:
    @pytest.mark.asyncio
    async def test_human_requested_true(self):
        router = MessageRouter(None, None)
        
        assert router._human_requested("I want to speak to an operator") == True
        assert router._human_requested("Give me a human") == True
        assert router._human_requested("позови оператора") == True
        assert router._human_requested("переведи на человека") == True
    
    @pytest.mark.asyncio
    async def test_human_requested_false(self):
        router = MessageRouter(None, None)
        
        assert router._human_requested("How do I reset my password?") == False
        assert router._human_requested("I have a question about billing") == False
    
    @pytest.mark.asyncio
    async def test_route_escalates_on_human_request(self, db: Database, sample_user_data: dict):
        ai_client = OpenAIClient(api_key="test_key", model="gpt-4")
        router = MessageRouter(ai_client, db)
        
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        response, escalated, ai_response = await router.route(
            message="I want to speak to an operator",
            ticket=ticket
        )
        
        assert escalated == True
        assert "оператор" in response.lower() or "operator" in response.lower()
        assert ticket.status == "human_handled"
    
    @pytest.mark.asyncio
    async def test_route_with_negative_sentiment(self, db: Database, sample_user_data: dict):
        ai_client = MagicMock(spec=OpenAIClient)
        ai_client.analyze_sentiment = AsyncMock(return_value=SentimentResult(
            sentiment="angry",
            score=0.15,
            emotions={"anger": 0.9},
            should_escalate=True
        ))
        
        router = MessageRouter(ai_client, db)
        
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        response, escalated, ai_response = await router.route(
            message="This is terrible!",
            ticket=ticket,
            user=user
        )
        
        assert escalated == True
        assert ticket.sentiment == "angry"
        assert ticket.sentiment_score == 0.15
    
    @pytest.mark.asyncio
    async def test_route_uses_faq(self, db: Database, sample_user_data: dict, sample_faq_data: dict):
        await db.create_faq(**sample_faq_data)
        
        ai_client = MagicMock(spec=OpenAIClient)
        ai_client.analyze_sentiment = AsyncMock(return_value=SentimentResult(
            sentiment="neutral",
            score=0.5,
            emotions={},
            should_escalate=False
        ))
        ai_client.detect_language = AsyncMock(return_value="en")
        ai_client.categorize_message = AsyncMock(return_value="account")
        ai_client.classify_priority = AsyncMock(return_value="normal")
        ai_client.should_escalate = AsyncMock(return_value=False)
        ai_client.generate_response = AsyncMock(return_value=MagicMock(
            content="Test response",
            confidence=0.9,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            used_faq=True,
            faq_id=1
        ))
        
        router = MessageRouter(ai_client, db)
        
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        response, escalated, ai_response = await router.route(
            message="How to reset password?",
            ticket=ticket,
            user=user
        )
        
        assert escalated == False
        assert ticket.category == "account"
        assert ticket.language == "en"
    
    @pytest.mark.asyncio
    async def test_route_sets_urgent_priority(self, db: Database, sample_user_data: dict):
        ai_client = MagicMock(spec=OpenAIClient)
        ai_client.analyze_sentiment = AsyncMock(return_value=SentimentResult(
            sentiment="frustrated",
            score=0.3,
            emotions={},
            should_escalate=False
        ))
        ai_client.detect_language = AsyncMock(return_value="ru")
        ai_client.categorize_message = AsyncMock(return_value="technical")
        ai_client.classify_priority = AsyncMock(return_value="urgent")
        
        router = MessageRouter(ai_client, db)
        
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        response, escalated, ai_response = await router.route(
            message="System is down!",
            ticket=ticket,
            user=user
        )
        
        assert ticket.priority == "urgent"
        assert escalated == True
    
    @pytest.mark.asyncio
    async def test_get_context(self, db: Database, sample_user_data: dict):
        ai_client = MagicMock(spec=OpenAIClient)
        router = MessageRouter(ai_client, db)
        
        user = await db.get_or_create_user(**sample_user_data)
        ticket = await db.create_ticket(user_id=user.id)
        
        await db.create_message(
            ticket_id=ticket.id,
            sender_type="user",
            content="User message"
        )
        await db.create_message(
            ticket_id=ticket.id,
            sender_type="ai",
            content="AI response"
        )
        
        context = await router._get_context(ticket)
        
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_format_faq_for_context(self, db: Database, sample_faq_data: dict):
        ai_client = MagicMock(spec=OpenAIClient)
        router = MessageRouter(ai_client, db)
        
        faq = await db.create_faq(**sample_faq_data)
        
        formatted = router._format_faq_for_context(faq)
        
        assert "Question:" in formatted
        assert "Answer:" in formatted
        assert faq.question in formatted
        assert faq.answer in formatted

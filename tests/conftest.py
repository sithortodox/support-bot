import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.models import Base
from core.database.crud import Database
from api.webhook import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    async with async_session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db(db_session: AsyncSession) -> Database:
    return Database(db_session)

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_openai_response():
    from unittest.mock import MagicMock
    from dataclasses import dataclass
    
    @dataclass
    class MockChoice:
        message: MagicMock
        finish_reason: str = "stop"
    
    @dataclass
    class MockUsage:
        prompt_tokens: int = 100
        completion_tokens: int = 50
        total_tokens: int = 150
    
    @dataclass
    class MockResponse:
        choices: list
        usage: MockUsage
    
    message = MagicMock()
    message.content = "Test response from AI"
    
    choice = MockChoice(message=message)
    usage = MockUsage()
    
    return MockResponse(choices=[choice], usage=usage)

@pytest.fixture
def sample_user_data():
    return {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def sample_ticket_data():
    return {
        "user_id": 1,
        "project_id": None,
        "priority": "normal"
    }

@pytest.fixture
def sample_message_data():
    return {
        "ticket_id": 1,
        "sender_type": "user",
        "sender_id": 123456789,
        "content": "Test message content"
    }

@pytest.fixture
def sample_faq_data():
    return {
        "question": "How to reset password?",
        "answer": "Go to Settings > Security > Reset Password",
        "keywords": "password, reset, security",
        "category": "account",
        "language": "en"
    }

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.ai.openai_client import OpenAIClient, AIResponse, SentimentResult

class TestOpenAIClient:
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_openai_response):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            response = await client.generate_response(
                message="Test message",
                system_prompt="Test prompt",
                ticket_history=[]
            )
            
            assert isinstance(response, AIResponse)
            assert response.content == "Test response from AI"
            assert response.prompt_tokens == 100
            assert response.completion_tokens == 50
            assert response.total_tokens == 150
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "sentiment": "frustrated",
            "score": 0.3,
            "emotions": {
                "frustration": 0.8,
                "anger": 0.2,
                "urgency": 0.5,
                "satisfaction": 0.1
            },
            "should_escalate": false
        }
        '''
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            sentiment = await client.analyze_sentiment("I'm having problems!")
            
            assert isinstance(sentiment, SentimentResult)
            assert sentiment.sentiment == "frustrated"
            assert sentiment.score == 0.3
            assert sentiment.emotions["frustration"] == 0.8
            assert sentiment.should_escalate == False
    
    @pytest.mark.asyncio
    async def test_detect_language_russian(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content.strip.return_value = "ru"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            language = await client.detect_language("Привет, как дела?")
            
            assert language == "ru"
    
    @pytest.mark.asyncio
    async def test_detect_language_english(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content.strip.return_value = "en"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            language = await client.detect_language("Hello, how are you?")
            
            assert language == "en"
    
    @pytest.mark.asyncio
    async def test_categorize_message(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content.strip.return_value = "technical"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            category = await client.categorize_message("My server is down!")
            
            assert category == "technical"
    
    @pytest.mark.asyncio
    async def test_classify_priority_urgent(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content.strip.return_value = "urgent"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            priority = await client.classify_priority("System is completely down!")
            
            assert priority == "urgent"
    
    @pytest.mark.asyncio
    async def test_should_escalate_true(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content.strip.return_value = "yes"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            escalate = await client.should_escalate("I want to speak to a human")
            
            assert escalate == True
    
    @pytest.mark.asyncio
    async def test_should_escalate_false(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content.strip.return_value = "no"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            escalate = await client.should_escalate("How do I change my password?")
            
            assert escalate == False
    
    def test_calculate_confidence_stop(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"
        
        confidence = client._calculate_confidence(mock_response)
        
        assert confidence == 0.85
    
    def test_calculate_confidence_length(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "length"
        
        confidence = client._calculate_confidence(mock_response)
        
        assert confidence == 0.5
    
    def test_cache_key_generation(self):
        client = OpenAIClient(api_key="test_key", model="gpt-4")
        
        key1 = client._get_cache_key("message1", "prompt1", None)
        key2 = client._get_cache_key("message1", "prompt1", None)
        key3 = client._get_cache_key("message2", "prompt1", None)
        
        assert key1 == key2
        assert key1 != key3

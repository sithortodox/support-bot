from openai import AsyncOpenAI
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import time
import json
import hashlib

@dataclass
class SentimentResult:
    sentiment: str
    score: float
    emotions: Dict[str, float] = field(default_factory=dict)
    should_escalate: bool = False

@dataclass
class AIResponse:
    content: str
    confidence: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    used_faq: bool = False
    faq_id: Optional[int] = None
    language: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[SentimentResult] = None

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self._cache: Dict[str, AIResponse] = {}
    
    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        ticket_history: List[dict],
        user_context: Optional[Dict[str, Any]] = None,
        faq_context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_cache: bool = True
    ) -> AIResponse:
        cache_key = self._get_cache_key(message, system_prompt, faq_context)
        
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        enhanced_system_prompt = self._build_system_prompt(
            system_prompt,
            user_context,
            faq_context
        )
        
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            *ticket_history[-15:],
            {"role": "user", "content": message}
        ]
        
        start_time = time.time()
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        confidence = self._calculate_confidence(response)
        
        ai_response = AIResponse(
            content=response.choices[0].message.content,
            confidence=confidence,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
        
        if use_cache and confidence > 0.8:
            self._cache[cache_key] = ai_response
            if len(self._cache) > 1000:
                self._cache.pop(next(iter(self._cache)))
        
        return ai_response
    
    def _build_system_prompt(
        self,
        base_prompt: str,
        user_context: Optional[Dict[str, Any]] = None,
        faq_context: Optional[str] = None
    ) -> str:
        prompt = base_prompt
        
        if user_context:
            recent_topics = user_context.get("recent_topics", [])
            if recent_topics:
                topics_str = ", ".join(recent_topics[:5])
                prompt += f"\n\nRecent topics discussed with this user: {topics_str}"
            
            preferred_language = user_context.get("preferred_language")
            if preferred_language:
                prompt += f"\n\nUser prefers communication in: {preferred_language}"
            
            avg_sentiment = user_context.get("avg_sentiment")
            if avg_sentiment and avg_sentiment < 0.3:
                prompt += "\n\nNote: This user has shown frustration in previous interactions. Be extra patient and empathetic."
        
        if faq_context:
            prompt += f"\n\nRelevant FAQ entries:\n{faq_context}"
        
        return prompt
    
    async def analyze_sentiment(
        self,
        message: str,
        ticket_history: Optional[str] = None
    ) -> SentimentResult:
        prompt = f"""Analyze the sentiment of this support message.

Message: {message}
{f"Context: {ticket_history}" if ticket_history else ""}

Respond in JSON format:
{{
    "sentiment": "positive/negative/neutral/frustrated/angry",
    "score": <float between 0 and 1, where 0 is very negative and 1 is very positive>,
    "emotions": {{
        "frustration": <float 0-1>,
        "anger": <float 0-1>,
        "urgency": <float 0-1>,
        "satisfaction": <float 0-1>
    }},
    "should_escalate": <true if human intervention recommended due to strong negative emotions>
}}

Consider:
- Frustration indicators: multiple questions, exclamation marks, short responses
- Anger indicators: ALL CAPS, aggressive language, threats
- Urgency: time-sensitive language, critical issues
- Context from ticket history"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return SentimentResult(
                sentiment=result.get("sentiment", "neutral"),
                score=result.get("score", 0.5),
                emotions=result.get("emotions", {}),
                should_escalate=result.get("should_escalate", False)
            )
        except (json.JSONDecodeError, KeyError):
            return SentimentResult(
                sentiment="neutral",
                score=0.5,
                should_escalate=False
            )
    
    async def detect_language(self, message: str) -> str:
        prompt = f"""Detect the language of this message. Respond with ISO 639-1 code only (e.g., "ru", "en", "de", "es", "fr").

Message: {message}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=5
        )
        
        language = response.choices[0].message.content.strip().lower()
        
        valid_codes = ["ru", "en", "de", "es", "fr", "it", "pt", "zh", "ja", "ko", "ar", "hi", "tr", "pl", "uk"]
        
        return language if language in valid_codes else "en"
    
    async def categorize_message(self, message: str) -> str:
        prompt = f"""Categorize this support message into one of these categories:
- technical: bugs, errors, technical issues
- billing: payments, subscriptions, refunds
- account: login, password, profile issues
- feature: feature requests, suggestions
- general: general questions, feedback
- other: doesn't fit other categories

Message: {message}

Respond with only the category name."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=20
        )
        
        category = response.choices[0].message.content.strip().lower()
        
        valid_categories = ["technical", "billing", "account", "feature", "general", "other"]
        
        return category if category in valid_categories else "general"
    
    async def classify_priority(self, message: str, sentiment: Optional[SentimentResult] = None) -> str:
        sentiment_info = ""
        if sentiment:
            sentiment_info = f"\nSentiment analysis: {sentiment.sentiment} (score: {sentiment.score})"
        
        prompt = f"""Analyze the following support message and classify its priority.
        
Message: {message}
{sentiment_info}

Respond with only one of these words: "low", "normal", "high", "urgent"

Consider:
- urgent: system down, critical bugs, security issues, data loss, very angry user
- high: major functionality broken, payment issues, frustrated user
- normal: questions, minor bugs, feature requests
- low: general inquiries, feedback, positive sentiment"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        if result in ["low", "normal", "high", "urgent"]:
            return result
        return "normal"
    
    async def should_escalate(
        self,
        message: str,
        sentiment: Optional[SentimentResult] = None,
        context: str = ""
    ) -> bool:
        if sentiment and sentiment.should_escalate:
            return True
        
        if sentiment and sentiment.score < 0.2:
            return True
        
        sentiment_info = ""
        if sentiment:
            sentiment_info = f"\nSentiment: {sentiment.sentiment} (score: {sentiment.score})"
            if sentiment.emotions:
                sentiment_info += f"\nEmotions: {sentiment.emotions}"
        
        prompt = f"""Determine if this support message requires human intervention.
        
Message: {message}
Context: {context}
{sentiment_info}

Respond with only "yes" or "no".

Escalate if:
- User explicitly requests human/operator
- Complex account/billing issues
- Sensitive data involved
- Multiple failed AI attempts
- Legal/compliance concerns
- Highly frustrated or angry user"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=5
        )
        
        return response.choices[0].message.content.strip().lower() == "yes"
    
    async def expand_context(
        self,
        message: str,
        user_context: Dict[str, Any]
    ) -> str:
        topics = user_context.get("recent_topics", [])
        if not topics:
            return ""
        
        prompt = f"""Based on the user's recent conversation topics and their current message, 
identify what additional context might be relevant.

Recent topics: {', '.join(topics)}
Current message: {message}

Respond with a brief summary of relevant context (1-2 sentences) or "none" if not applicable."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        result = response.choices[0].message.content.strip()
        return result if result.lower() != "none" else ""
    
    def _calculate_confidence(self, response) -> float:
        if response.choices[0].finish_reason == "stop":
            return 0.85
        elif response.choices[0].finish_reason == "length":
            return 0.5
        return 0.7
    
    def _get_cache_key(self, message: str, system_prompt: str, faq_context: Optional[str]) -> str:
        content = f"{message}|{system_prompt}|{faq_context or ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def clear_cache(self):
        self._cache.clear()

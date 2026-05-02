from openai import AsyncOpenAI
from typing import List, Optional
from dataclasses import dataclass
import time

@dataclass
class AIResponse:
    content: str
    confidence: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        ticket_history: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            *ticket_history[-10:],
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
        
        return AIResponse(
            content=response.choices[0].message.content,
            confidence=confidence,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
    
    def _calculate_confidence(self, response) -> float:
        if response.choices[0].finish_reason == "stop":
            return 0.85
        elif response.choices[0].finish_reason == "length":
            return 0.5
        return 0.7
    
    async def classify_priority(self, message: str) -> str:
        prompt = f"""Analyze the following support message and classify its priority.
        
Message: {message}

Respond with only one of these words: "low", "normal", "high", "urgent"

Consider:
- urgent: system down, critical bugs, security issues
- high: major functionality broken, payment issues
- normal: questions, minor bugs, feature requests
- low: general inquiries, feedback"""

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
    
    async def should_escalate(self, message: str, context: str = "") -> bool:
        prompt = f"""Determine if this support message requires human intervention.
        
Message: {message}
Context: {context}

Respond with only "yes" or "no".

Escalate if:
- User explicitly requests human/operator
- Complex account/billing issues
- Sensitive data involved
- Multiple failed AI attempts
- Legal/compliance concerns"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=5
        )
        
        return response.choices[0].message.content.strip().lower() == "yes"

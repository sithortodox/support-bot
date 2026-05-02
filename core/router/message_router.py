from typing import Optional, List, TYPE_CHECKING
from ..ai.openai_client import OpenAIClient, AIResponse
from ..ai.prompts import get_system_prompt

if TYPE_CHECKING:
    from ..database.crud import Database
    from ..database.models import Ticket, Project

class MessageRouter:
    HUMAN_TRIGGERS = [
        "оператор",
        "человек",
        "админ",
        "поговорить с человеком",
        "связаться с оператором",
        "перевод на оператора",
        "живой человек",
        "сотрудник"
    ]
    
    def __init__(self, openai_client: OpenAIClient, db: "Database"):
        self.ai = openai_client
        self.db = db
    
    async def route(
        self,
        message: str,
        ticket: "Ticket",
        project: Optional["Project"] = None
    ) -> tuple[str, bool, Optional[AIResponse]]:
        if self._human_requested(message):
            return await self._escalate_to_human(ticket), True, None
        
        if ticket.priority in ["urgent"]:
            return await self._escalate_to_human(ticket), True, None
        
        if ticket.status == "human_handled":
            return "Ожидайте ответа оператора.", False, None
        
        history = await self._get_context(ticket)
        system_prompt = get_system_prompt(
            project_name=project.name if project else None,
            custom_prompt=project.system_prompt if project else None
        )
        
        ai_response = await self.ai.generate_response(
            message=message,
            system_prompt=system_prompt,
            ticket_history=history
        )
        
        should_escalate = await self.ai.should_escalate(message, "\n".join([h["content"] for h in history]))
        
        if should_escalate or ai_response.confidence < 0.6:
            escalation_msg = await self._escalate_to_human(ticket, ai_response.content)
            return escalation_msg, True, ai_response
        
        return ai_response.content, False, ai_response
    
    def _human_requested(self, message: str) -> bool:
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in self.HUMAN_TRIGGERS)
    
    async def _escalate_to_human(
        self,
        ticket: "Ticket",
        partial_response: Optional[str] = None
    ) -> str:
        ticket.status = "human_handled"
        await self.db.session.commit()
        
        await self._notify_admins(ticket)
        
        if partial_response:
            return f"{partial_response}\n\nВаш запрос передан оператору для уточнения. Ожидайте."
        
        return "Ваш запрос передан оператору. Ожидайте ответа."
    
    async def _get_context(self, ticket: "Ticket") -> List[dict]:
        messages = await self.db.get_ticket_messages(ticket.id)
        
        context = []
        for msg in messages:
            role = "user" if msg.sender_type == "user" else "assistant"
            context.append({"role": role, "content": msg.content})
        
        return context
    
    async def _notify_admins(self, ticket: "Ticket"):
        pass

    async def classify_priority(self, message: str) -> str:
        return await self.ai.classify_priority(message)

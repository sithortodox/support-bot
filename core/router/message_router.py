from typing import Optional, List, Dict, Any, TYPE_CHECKING
from ..ai.openai_client import OpenAIClient, AIResponse, SentimentResult
from ..ai.prompts import get_system_prompt
import logging

if TYPE_CHECKING:
    from ..database.crud import Database
    from ..database.models import Ticket, Project, FAQ, User

logger = logging.getLogger(__name__)

class MessageRouter:
    HUMAN_TRIGGERS = [
        "оператор",
        "человек",
        "админ",
        "поговорить с человеком",
        "связаться с оператором",
        "перевод на оператора",
        "живой человек",
        "сотрудник",
        "agent",
        "human",
        "operator",
        "support agent"
    ]
    
    def __init__(self, openai_client: OpenAIClient, db: "Database"):
        self.ai = openai_client
        self.db = db
    
    async def route(
        self,
        message: str,
        ticket: "Ticket",
        project: Optional["Project"] = None,
        user: Optional["User"] = None
    ) -> tuple[str, bool, Optional[AIResponse]]:
        if self._human_requested(message):
            return await self._escalate_to_human(ticket), True, None
        
        sentiment = await self.ai.analyze_sentiment(message)
        logger.info(f"Sentiment for ticket {ticket.id}: {sentiment.sentiment} ({sentiment.score})")
        
        await self.db.update_ticket_sentiment(ticket.id, sentiment.sentiment, sentiment.score)
        
        if sentiment.should_escalate:
            return await self._escalate_to_human(
                ticket,
                reason="Negative sentiment detected"
            ), True, None
        
        language = await self.ai.detect_language(message)
        await self.db.update_ticket_language(ticket.id, language)
        
        category = await self.ai.categorize_message(message)
        await self.db.update_ticket_category(ticket.id, category)
        
        priority = await self.ai.classify_priority(message, sentiment)
        ticket.priority = priority
        await self.db.session.commit()
        
        if priority == "urgent":
            return await self._escalate_to_human(
                ticket,
                reason="Urgent priority"
            ), True, None
        
        if ticket.status == "human_handled":
            return "Ожидайте ответа оператора.", False, None
        
        faq_match = await self._search_faq(message, project, language)
        
        user_context = await self._get_user_context(user) if user else None
        
        history = await self._get_context(ticket)
        
        faq_context = None
        used_faq = False
        faq_id = None
        
        if faq_match:
            faq_context = self._format_faq_for_context(faq_match)
            used_faq = True
            faq_id = faq_match.id
            await self.db.increment_faq_use(faq_match.id)
        
        system_prompt = get_system_prompt(
            project_name=project.name if project else None,
            custom_prompt=project.system_prompt if project else None,
            language=language,
            category=category
        )
        
        ai_response = await self.ai.generate_response(
            message=message,
            system_prompt=system_prompt,
            ticket_history=history,
            user_context=user_context,
            faq_context=faq_context
        )
        
        ai_response.used_faq = used_faq
        ai_response.faq_id = faq_id
        ai_response.language = language
        ai_response.category = category
        ai_response.sentiment = sentiment
        
        if user:
            await self.db.update_user_context(
                user_id=user.id,
                topic=category,
                language=language,
                sentiment_score=sentiment.score
            )
        
        should_escalate = await self.ai.should_escalate(
            message,
            sentiment,
            "\n".join([h["content"] for h in history])
        )
        
        if should_escalate or ai_response.confidence < 0.6:
            escalation_msg = await self._escalate_to_human(
                ticket,
                partial_response=ai_response.content,
                reason="Low confidence or escalation needed"
            )
            return escalation_msg, True, ai_response
        
        return ai_response.content, False, ai_response
    
    def _human_requested(self, message: str) -> bool:
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in self.HUMAN_TRIGGERS)
    
    async def _escalate_to_human(
        self,
        ticket: "Ticket",
        partial_response: Optional[str] = None,
        reason: Optional[str] = None
    ) -> str:
        ticket.status = "human_handled"
        await self.db.session.commit()
        
        await self._notify_admins(ticket, reason)
        
        logger.info(f"Ticket {ticket.id} escalated to human. Reason: {reason}")
        
        if partial_response:
            return f"{partial_response}\n\nВаш запрос передан оператору для уточнения. Ожидайте."
        
        return "Ваш запрос передан оператору. Ожидайте ответа."
    
    async def _get_context(self, ticket: "Ticket") -> List[dict]:
        messages = await self.db.get_ticket_messages(ticket.id, limit=20)
        
        context = []
        for msg in messages:
            role = "user" if msg.sender_type == "user" else "assistant"
            context.append({"role": role, "content": msg.content})
        
        return context
    
    async def _get_user_context(self, user: "User") -> Optional[Dict[str, Any]]:
        try:
            context = await self.db.get_or_create_user_context(user.id)
            
            recent_topics = []
            if context.recent_topics:
                recent_topics = [t for t in context.recent_topics.split("|") if t][:10]
            
            return {
                "recent_topics": recent_topics,
                "preferred_language": context.preferred_language,
                "avg_sentiment": context.avg_sentiment,
                "total_messages": context.total_messages
            }
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return None
    
    async def _search_faq(
        self,
        message: str,
        project: Optional["Project"],
        language: str
    ) -> Optional["FAQ"]:
        try:
            faqs = await self.db.search_faq(
                query=message,
                project_id=project.id if project else None,
                language=language,
                limit=1
            )
            
            if faqs:
                logger.info(f"FAQ match found for message: {message[:50]}")
                return faqs[0]
            
            return None
        except Exception as e:
            logger.error(f"Error searching FAQ: {e}")
            return None
    
    def _format_faq_for_context(self, faq: "FAQ") -> str:
        return f"Question: {faq.question}\nAnswer: {faq.answer}\nKeywords: {faq.keywords or 'N/A'}"
    
    async def _notify_admins(self, ticket: "Ticket", reason: Optional[str] = None):
        try:
            admins = await self.db.get_admin_users()
            
            if not admins:
                return
            
            from aiogram import Bot
            from core.config import BOT_TOKEN
            
            bot = Bot(token=BOT_TOKEN)
            
            user_info = ticket.user.username or ticket.user.telegram_id
            sentiment_info = f"Sentiment: {ticket.sentiment} ({ticket.sentiment_score:.2f})" if ticket.sentiment else ""
            
            for admin in admins:
                try:
                    text = f"🔔 Новый тикет #{ticket.id}\n\n"
                    text += f"👤 Пользователь: {user_info}\n"
                    text += f"📂 Категория: {ticket.category or 'Не определена'}\n"
                    text += f"⚡ Приоритет: {ticket.priority}\n"
                    text += f"🌐 Язык: {ticket.language or 'Не определен'}\n"
                    if sentiment_info:
                        text += f"{sentiment_info}\n"
                    if reason:
                        text += f"📝 Причина эскалации: {reason}\n"
                    
                    await bot.send_message(
                        chat_id=admin.telegram_id,
                        text=text
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin.telegram_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")

    async def classify_priority(self, message: str) -> str:
        sentiment = await self.ai.analyze_sentiment(message)
        return await self.ai.classify_priority(message, sentiment)

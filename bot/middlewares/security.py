from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.crud import Database
from core.config import ADMIN_IDS
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool
        
        self.default_limits = {
            "message": {"max": 20, "window": 60},
            "callback": {"max": 30, "window": 60},
            "ticket": {"max": 5, "window": 300}
        }
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        
        if not user:
            return await handler(event, data)
        
        if user.id in ADMIN_IDS:
            data["is_admin"] = True
            return await handler(event, data)
        
        async with self.session_pool() as session:
            db = Database(session)
            data["db"] = db
            data["session"] = session
            data["is_admin"] = False
            
            is_blocked, reason = await db.is_user_blocked(user.id)
            
            if is_blocked:
                logger.warning(f"Blocked user {user.id} attempted action")
                
                if isinstance(event, Message):
                    await event.answer(
                        f"⛔ Ваш аккаунт заблокирован.\n"
                        f"Причина: {reason or 'Не указана'}\n\n"
                        f"Обратитесь к администратору для разблокировки."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        f"⛔ Аккаунт заблокирован",
                        show_alert=True
                    )
                return
            
            action_type = self._get_action_type(event)
            
            if action_type:
                limits = self.default_limits.get(action_type, {"max": 10, "window": 60})
                
                allowed, remaining = await db.check_rate_limit(
                    user_id=user.id,
                    action_type=action_type,
                    max_attempts=limits["max"],
                    window_minutes=limits["window"]
                )
                
                if not allowed:
                    logger.warning(f"Rate limit exceeded for user {user.id}, action: {action_type}")
                    
                    if isinstance(event, Message):
                        await event.answer(
                            f"⚠️ Превышен лимит запросов.\n"
                            f"Подождите немного перед следующим действием."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "⚠️ Превышен лимит запросов",
                            show_alert=True
                        )
                    return
            
            if isinstance(event, Message) and event.text:
                spam_filter = await db.check_spam(event.text)
                
                if spam_filter:
                    logger.warning(f"Spam detected from user {user.id}: {spam_filter.pattern}")
                    
                    if spam_filter.action == "block":
                        await db.block_user(
                            user_id=user.id,
                            blocked_by=0,
                            reason=f"Спам: {spam_filter.pattern}",
                            block_type="spam"
                        )
                        await event.answer("⛔ Вы заблокированы за спам.")
                        return
                    
                    elif spam_filter.action == "warn":
                        await event.answer(
                            f"⚠️ Ваше сообщение похоже на спам.\n"
                            f"Пожалуйста, соблюдайте правила общения."
                        )
                        return
            
            return await handler(event, data)
    
    def _get_action_type(self, event: TelegramObject) -> str:
        if isinstance(event, Message):
            return "message"
        elif isinstance(event, CallbackQuery):
            return "callback"
        return ""
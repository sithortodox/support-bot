from aiogram.types import InlineKeyboardMarkup
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageFormatter:
    @staticmethod
    def ticket_card(
        ticket_id: int,
        status: str,
        priority: str,
        category: Optional[str],
        user_name: str,
        created_at: datetime,
        sentiment: Optional[str] = None,
        language: Optional[str] = None,
        response_time: Optional[float] = None
    ) -> str:
        status_config = {
            "open": {"emoji": "🟢", "text": "Открыт"},
            "human_handled": {"emoji": "🟡", "text": "В работе"},
            "closed": {"emoji": "⚫", "text": "Закрыт"},
            "ai_handled": {"emoji": "🤖", "text": "AI обрабатывает"}
        }
        
        priority_config = {
            "urgent": {"emoji": "🔴", "text": "Срочно"},
            "high": {"emoji": "🟠", "text": "Высокий"},
            "normal": {"emoji": "🔵", "text": "Обычный"},
            "low": {"emoji": "⚪", "text": "Низкий"}
        }
        
        status_info = status_config.get(status, {"emoji": "⚪", "text": status})
        priority_info = priority_config.get(priority, {"emoji": "⚪", "text": priority})
        
        card = f"""
┌──────────────────────────┐
│ 🎫 Тикет #{ticket_id}
├──────────────────────────┤
│ {status_info['emoji']} Статус: {status_info['text']}
│ {priority_info['emoji']} Приоритет: {priority_info['text']}
│ 📂 Категория: {category or 'Не указана'}
│ 👤 Пользователь: {user_name}
│ 📅 Создан: {created_at.strftime('%d.%m.%Y %H:%M')}
"""
        
        if sentiment:
            sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😟", "frustrated": "😤"}.get(sentiment, "😐")
            card += f"│ {sentiment_emoji} Настроение: {sentiment.title()}\n"
        
        if language:
            lang_emoji = {"ru": "🇷🇺", "en": "🇬🇧"}.get(language, "🌐")
            card += f"│ {lang_emoji} Язык: {language.upper()}\n"
        
        if response_time:
            card += f"│ ⏱️ Время ответа: {response_time:.1f} мин\n"
        
        card += "└──────────────────────────┘"
        
        return card
    
    @staticmethod
    def message_bubble(
        sender: str,
        content: str,
        timestamp: datetime,
        rating: Optional[str] = None
    ) -> str:
        sender_config = {
            "user": {"emoji": "👤", "name": "Вы"},
            "ai": {"emoji": "🤖", "name": "AI Ассистент"},
            "admin": {"emoji": "👨‍💼", "name": "Оператор"},
            "system": {"emoji": "ℹ️", "name": "Система"}
        }
        
        sender_info = sender_config.get(sender, {"emoji": "💬", "name": sender})
        
        rating_str = ""
        if rating == "positive":
            rating_str = " 👍"
        elif rating == "negative":
            rating_str = " 👎"
        
        return f"""
{sender_info['emoji']} <b>{sender_info['name']}</b>{rating_str}
<time>{timestamp.strftime('%H:%M')}</time>

{content}
"""
    
    @staticmethod
    def stats_dashboard(
        total_tickets: int,
        open_tickets: int,
        closed_tickets: int,
        avg_response_time: Optional[float] = None,
        satisfaction_rate: Optional[float] = None
    ) -> str:
        dashboard = f"""
╔══════════════════════════╗
║      📊 СТАТИСТИКА       ║
╠══════════════════════════╣
║ 📋 Всего тикетов: {total_tickets:>6} ║
║ 🟢 Открытых: {open_tickets:>11} ║
║ ⚫ Закрытых: {closed_tickets:>11} ║
"""
        
        if avg_response_time:
            dashboard += f"║ ⏱️ Ср. время: {avg_response_time:>8.1f}м ║\n"
        
        if satisfaction_rate is not None:
            satisfaction_emoji = "😊" if satisfaction_rate >= 80 else "😐" if satisfaction_rate >= 50 else "😟"
            dashboard += f"║ {satisfaction_emoji} Удовлетворенность: {satisfaction_rate:>4.0f}% ║\n"
        
        dashboard += "╚══════════════════════════╝"
        
        return dashboard
    
    @staticmethod
    def ai_cost_report(
        requests: int,
        total_tokens: int,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost: float,
        period: str = "24 часа"
    ) -> str:
        return f"""
┌────────────────────────────┐
│    💰 РАСХОДЫ OpenAI       │
│    📅 За {period}
├────────────────────────────┤
│ 🤖 Запросов: {requests:>13} │
│ 📊 Токенов: {total_tokens:>14} │
│    ├ Prompt: {prompt_tokens:>12} │
│    └ Completion: {completion_tokens:>7} │
│                            │
│ 💵 Стоимость: ${estimated_cost:>9.4f} │
└────────────────────────────┘
"""
    
    @staticmethod
    def help_message() -> str:
        return """
┌──────────────────────────────┐
│         📚 ПОМОЩЬ            │
├──────────────────────────────┤
│                              │
│ 🎫 <b>Тикеты</b>              │
│ • Создайте тикет кнопкой     │
│   "Задать вопрос"            │
│ • Отслеживайте статус        │
│ • Получайте ответы от AI    │
│   или оператора              │
│                              │
│ 🤖 <b>AI Ассистент</b>        │
│ • Мгновенные ответы          │
│ • Категоризация вопросов     │
│ • Определение срочности      │
│                              │
│ 👨‍💼 <b>Оператор</b>          │
│ • Напишите "оператор"        │
│ • Для сложных вопросов       │
│                              │
│ ⭐ <b>Оценка</b>             │
│ • Оценивайте ответы          │
│ • Помогайте улучшать AI      │
│                              │
├──────────────────────────────┤
│ Быстрые команды:             │
│ /start - Главное меню        │
│ /status - Мои тикеты        │
│ /operator - Позвать оператора│
└──────────────────────────────┘
"""
    
    @staticmethod
    def welcome_message(user_name: str) -> str:
        return f"""
┌──────────────────────────────┐
│   👋 Привет, {user_name}!     │
├──────────────────────────────┤
│                              │
│ Добро пожаловать в систему  │
│ технической поддержки!       │
│                              │
│ 🤖 AI ответит мгновенно      │
│ 👨‍💼 Оператор поможет         │
│    при сложных вопросах      │
│                              │
│ 💡 Выберите действие ниже    │
└──────────────────────────────┘
"""
    
    @staticmethod
    def category_selection() -> str:
        return """
┌──────────────────────────────┐
│   📂 Выберите категорию      │
├──────────────────────────────┤
│                              │
│ 📁 <b>Категория поможет:</b> │
│ • Быстрее найти решение      │
│ • Определить приоритет       │
│ • Выбрать специалиста        │
│                              │
│ Если не знаете - выберите    │
│ "Другой вопрос"              │
└──────────────────────────────┘
"""
    
    @staticmethod
    def ticket_created(ticket_id: int, category: str = None) -> str:
        return f"""
┌──────────────────────────────┐
│   ✅ Тикет создан!           │
├──────────────────────────────┤
│                              │
│ 🎫 Номер: #{ticket_id}        │
│ 📂 Категория: {category or 'Общий'}
│                              │
│ 🤖 AI обрабатывает ваш       │
│    запрос...                 │
│                              │
│ 💡 Хотите оператора?         │
│    Напишите "оператор"       │
└──────────────────────────────┘
"""
    
    @staticmethod
    def escalation_message(reason: str = None) -> str:
        msg = """
┌──────────────────────────────┐
│   👨‍💼 Оператор в пути         │
├──────────────────────────────┤
│                              │
│ Ваш запрос передан           │
│ специалисту поддержки.        │
│                              │
│ ⏱️ Ожидайте ответа           │
"""
        if reason:
            msg += f"\n│ 📝 {reason}\n"
        
        msg += "└──────────────────────────────┘"
        return msg
    
    @staticmethod
    def admin_welcome(admin_name: str, stats: dict) -> str:
        return f"""
┌──────────────────────────────┐
│ 🔧 Админ-панель              │
│ 👨‍💼 {admin_name}              │
├──────────────────────────────┤
│ 📊 <b>Сейчас:</b>            │
│ 🟢 Открытых: {stats.get('open', 0):>13} │
│ 🟡 В работе: {stats.get('progress', 0):>12} │
│ 🔴 Срочных: {stats.get('urgent', 0):>13} │
└──────────────────────────────┘
"""
    
    @staticmethod
    def security_alert(
        alert_type: str,
        user_id: int,
        reason: str = None
    ) -> str:
        alert = f"""
⚠️ <b>ВНИМАНИЕ</b>

🚨 <b>Тип:</b> {alert_type}
👤 <b>User ID:</b> {user_id}
"""
        if reason:
            alert += f"\n📝 <b>Причина:</b> {reason}"
        
        return alert

formatter = MessageFormatter()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Optional

class ModernKeyboards:
    @staticmethod
    def user_main_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="💬 Задать вопрос", callback_data="new_ticket")
        )
        builder.row(
            InlineKeyboardButton(text="📋 Мои тикеты", callback_data="my_tickets"),
            InlineKeyboardButton(text="📊 Статус", callback_data="my_status")
        )
        builder.row(
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def categories_menu(categories: List, back_data: str = "main_menu") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        for category in categories:
            emoji = category.emoji or "📁"
            builder.row(
                InlineKeyboardButton(
                    text=f"{emoji} {category.name.title()}",
                    callback_data=f"category_{category.id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="❓ Другой вопрос", callback_data="category_other")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Главное меню", callback_data=back_data)
        )
        
        return builder.as_markup()
    
    @staticmethod
    def ticket_menu(ticket_id: int, is_admin: bool = False, ticket_status: str = "open") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        if is_admin:
            builder.row(
                InlineKeyboardButton(text="💬 Ответить", callback_data=f"answer_{ticket_id}"),
                InlineKeyboardButton(text="📝 Шаблоны", callback_data=f"templates_{ticket_id}")
            )
            builder.row(
                InlineKeyboardButton(text="⚡ Срочно", callback_data=f"priority_high_{ticket_id}"),
                InlineKeyboardButton(text="📌 Назначить", callback_data=f"assign_{ticket_id}")
            )
            
            if ticket_status != "closed":
                builder.row(
                    InlineKeyboardButton(text="✅ Закрыть", callback_data=f"close_{ticket_id}")
                )
        else:
            if ticket_status == "open":
                builder.row(
                    InlineKeyboardButton(text="👤 Позвать оператора", callback_data=f"escalate_{ticket_id}")
                )
            
            if ticket_status != "closed":
                builder.row(
                    InlineKeyboardButton(text="📎 Добавить файл", callback_data=f"attach_{ticket_id}"),
                    InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"close_{ticket_id}")
                )
        
        builder.row(
            InlineKeyboardButton(text="🔙 К списку", callback_data="my_tickets")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def rating_menu(message_id: int, ticket_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="👍 Отлично", callback_data=f"rate_positive_{message_id}"),
            InlineKeyboardButton(text="👎 Не помогло", callback_data=f"rate_negative_{message_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 К тикету", callback_data=f"view_ticket_{ticket_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def tickets_list(tickets: List, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        start = page * per_page
        end = start + per_page
        page_tickets = tickets[start:end]
        
        for ticket in page_tickets:
            status_icons = {
                "open": "🟢",
                "human_handled": "🟡", 
                "closed": "⚫",
                "ai_handled": "🤖"
            }
            status_icon = status_icons.get(ticket.status, "⚪")
            
            priority_icons = {
                "urgent": "🔴",
                "high": "🟠",
                "normal": "🔵",
                "low": "⚪"
            }
            priority_icon = priority_icons.get(ticket.priority, "")
            
            username = ticket.user.username or f"ID:{ticket.user.telegram_id}"
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_icon} #{ticket.id} {priority_icon} @{username}",
                    callback_data=f"view_ticket_{ticket.id}"
                )
            )
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"tickets_page_{page-1}")
            )
        
        if end < len(tickets):
            nav_buttons.append(
                InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"tickets_page_{page+1}")
            )
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.row(
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)
        )
        return builder.as_markup()
    
    @staticmethod
    def confirm_action(action: str, item_id: int, confirm_text: str = "✅ Да", cancel_text: str = "❌ Нет") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text=confirm_text, callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton(text=cancel_text, callback_data=f"cancel_{action}_{item_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def language_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🌐 Язык", callback_data="change_language"),
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        )
        
        return builder.as_markup()

class AdminKeyboards:
    @staticmethod
    def admin_main() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📋 Тикеты", callback_data="admin_tickets"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        )
        builder.row(
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton(text="🔐 Безопасность", callback_data="admin_security")
        )
        builder.row(
            InlineKeyboardButton(text="📚 FAQ", callback_data="admin_faq"),
            InlineKeyboardButton(text="📝 Шаблоны", callback_data="admin_templates")
        )
        builder.row(
            InlineKeyboardButton(text="📈 Аналитика", callback_data="admin_analytics"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def tickets_filter() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🟢 Открытые", callback_data="admin_tickets_open"),
            InlineKeyboardButton(text="🟡 В работе", callback_data="admin_tickets_progress")
        )
        builder.row(
            InlineKeyboardButton(text="🔴 Срочные", callback_data="admin_tickets_urgent"),
            InlineKeyboardButton(text="⚫ Закрытые", callback_data="admin_tickets_closed")
        )
        builder.row(
            InlineKeyboardButton(text="📋 Все", callback_data="admin_tickets_all")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def ticket_admin_actions(ticket_id: int, status: str = "open") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="💬 Ответить", callback_data=f"answer_{ticket_id}"),
            InlineKeyboardButton(text="📝 Шаблон", callback_data=f"templates_{ticket_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="⚡ Urgent", callback_data=f"priority_urgent_{ticket_id}"),
            InlineKeyboardButton(text="🔥 High", callback_data=f"priority_high_{ticket_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="📌 Назначить себе", callback_data=f"assign_self_{ticket_id}"),
            InlineKeyboardButton(text="👥 Передать", callback_data=f"assign_other_{ticket_id}")
        )
        
        if status != "closed":
            builder.row(
                InlineKeyboardButton(text="✅ Закрыть с комментарием", callback_data=f"close_comment_{ticket_id}"),
                InlineKeyboardButton(text="✅ Закрыть", callback_data=f"close_{ticket_id}")
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 К списку", callback_data="admin_tickets")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def security_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🚫 Блокировки", callback_data="admin_blocks"),
            InlineKeyboardButton(text="📊 Лимиты", callback_data="admin_ratelimits")
        )
        builder.row(
            InlineKeyboardButton(text="🛡️ Спам-фильтры", callback_data="admin_spam"),
            InlineKeyboardButton(text="📋 Логи", callback_data="admin_audit")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def templates_list(templates: List, ticket_id: int = None) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        for template in templates[:8]:
            builder.row(
                InlineKeyboardButton(
                    text=f"📝 {template.name}",
                    callback_data=f"template_{template.id}" + (f"_{ticket_id}" if ticket_id else "")
                )
            )
        
        if ticket_id:
            builder.row(
                InlineKeyboardButton(text="✍️ Свой ответ", callback_data=f"custom_answer_{ticket_id}")
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_ticket_{ticket_id}" if ticket_id else "admin_templates")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def quick_stats(stats: dict) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text=f"🟢 Открытых: {stats.get('open', 0)}", callback_data="admin_tickets_open")
        )
        builder.row(
            InlineKeyboardButton(text=f"🟡 В работе: {stats.get('progress', 0)}", callback_data="admin_tickets_progress")
        )
        builder.row(
            InlineKeyboardButton(text=f"🔴 Срочных: {stats.get('urgent', 0)}", callback_data="admin_tickets_urgent")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Подробнее", callback_data="admin_stats_detailed"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def admin_analytics() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🤖 AI метрики", callback_data="admin_ai_stats"),
            InlineKeyboardButton(text="⭐ Удовлетворенность", callback_data="admin_satisfaction")
        )
        builder.row(
            InlineKeyboardButton(text="📂 По категориям", callback_data="admin_categories_stats"),
            InlineKeyboardButton(text="😊 Сентимент", callback_data="admin_sentiment_stats")
        )
        builder.row(
            InlineKeyboardButton(text="📈 График активности", callback_data="admin_activity"),
            InlineKeyboardButton(text="💰 Расходы OpenAI", callback_data="admin_costs")
        )
        builder.row(
            InlineKeyboardButton(text="📥 Экспорт данных", callback_data="admin_export")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")
        )
        
        return builder.as_markup()

user_keyboards = ModernKeyboards()
admin_keyboards = AdminKeyboards()

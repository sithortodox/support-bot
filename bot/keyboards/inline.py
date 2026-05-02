from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Новый вопрос", callback_data="new_ticket")
    builder.button(text="📋 Мои тикеты", callback_data="my_tickets")
    builder.button(text="ℹ️ Помощь", callback_data="help")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_projects_keyboard(projects: List) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.button(text=project.name, callback_data=f"project_{project.id}")
    builder.adjust(1)
    return builder.as_markup()

def get_ticket_actions_keyboard(ticket_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if is_admin:
        builder.button(text="💬 Ответить", callback_data=f"answer_{ticket_id}")
        builder.button(text="✅ Закрыть", callback_data=f"close_{ticket_id}")
        builder.button(text="⚡ Высокий приоритет", callback_data=f"priority_{ticket_id}")
    else:
        builder.button(text="👤 Оператор", callback_data=f"escalate_{ticket_id}")
        builder.button(text="✅ Закрыть тикет", callback_data=f"close_{ticket_id}")
    
    builder.adjust(2)
    return builder.as_markup()

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Открытые тикеты", callback_data="admin_tickets")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="⚙️ Настройки", callback_data="admin_settings")
    builder.adjust(2)
    return builder.as_markup()

def get_tickets_list_keyboard(tickets: List, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for ticket in tickets:
        status_emoji = {"open": "🟢", "human_handled": "🟡", "closed": "🔴"}.get(ticket.status, "⚪")
        builder.button(
            text=f"{status_emoji} #{ticket.id} - {ticket.user.username or ticket.user.telegram_id}",
            callback_data=f"view_ticket_{ticket.id}"
        )
    
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_keyboard(action: str, ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"confirm_{action}_{ticket_id}")
    builder.button(text="❌ Нет", callback_data=f"cancel_{action}_{ticket_id}")
    builder.adjust(2)
    return builder.as_markup()

def get_categories_keyboard(categories: List) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        emoji = category.emoji or "📁"
        builder.button(
            text=f"{emoji} {category.name}",
            callback_data=f"category_{category.id}"
        )
    
    builder.button(text="❓ Другое", callback_data="category_other")
    builder.adjust(2)
    return builder.as_markup()

def get_rating_keyboard(message_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👍 Полезно", callback_data=f"rate_positive_{message_id}")
    builder.button(text="👎 Не помогло", callback_data=f"rate_negative_{message_id}")
    builder.adjust(2)
    return builder.as_markup()

def get_templates_keyboard(templates: List, ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for template in templates:
        builder.button(
            text=f"📝 {template.name}",
            callback_data=f"template_{template.id}_{ticket_id}"
        )
    
    builder.button(text="✍️ Свой ответ", callback_data=f"custom_answer_{ticket_id}")
    builder.button(text="🔙 Назад", callback_data=f"view_ticket_{ticket_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_ticket_detail_keyboard(
    ticket_id: int,
    is_admin: bool = False,
    has_rating: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if is_admin:
        builder.button(text="💬 Ответить", callback_data=f"answer_{ticket_id}")
        builder.button(text="📋 Шаблоны", callback_data=f"templates_{ticket_id}")
        builder.button(text="✅ Закрыть", callback_data=f"close_{ticket_id}")
        builder.button(text="⚡ Приоритет", callback_data=f"priority_{ticket_id}")
        builder.adjust(2)
    else:
        builder.button(text="👤 Оператор", callback_data=f"escalate_{ticket_id}")
        builder.button(text="✅ Закрыть", callback_data=f"close_{ticket_id}")
        if not has_rating:
            builder.button(text="⭐ Оценить", callback_data=f"rate_ticket_{ticket_id}")
        builder.adjust(2)
    
    return builder.as_markup()

def get_eta_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Место в очереди", callback_data=f"queue_{ticket_id}")
    builder.button(text="⏱️ Ожидаемое время", callback_data=f"eta_{ticket_id}")
    builder.button(text="🔙 К тикету", callback_data=f"view_ticket_{ticket_id}")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_attachments_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📎 Добавить вложение", callback_data=f"attach_{ticket_id}")
    builder.button(text="📥 Скачать вложения", callback_data=f"download_{ticket_id}")
    builder.button(text="🔙 Назад", callback_data=f"view_ticket_{ticket_id}")
    builder.adjust(1)
    return builder.as_markup()

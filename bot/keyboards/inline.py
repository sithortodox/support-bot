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

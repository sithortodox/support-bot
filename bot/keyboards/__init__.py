from .inline import ModernKeyboards, AdminKeyboards
from .formatter import formatter, MessageFormatter

def get_main_menu_keyboard():
    return ModernKeyboards.user_main_menu()

def get_projects_keyboard():
    return ModernKeyboards.user_main_menu()

def get_categories_keyboard(categories):
    return ModernKeyboards.categories_menu(categories)

def get_tickets_list_keyboard(tickets, page=0):
    return ModernKeyboards.tickets_list(tickets, page)

def get_ticket_detail_keyboard(ticket_id, is_admin=False, ticket_status="open"):
    return ModernKeyboards.ticket_menu(ticket_id, is_admin, ticket_status)

def get_ticket_actions_keyboard(ticket_id, is_admin=False, ticket_status="open"):
    if is_admin:
        return AdminKeyboards.ticket_admin_actions(ticket_id, ticket_status)
    return ModernKeyboards.ticket_menu(ticket_id, is_admin, ticket_status)

def get_rating_keyboard(message_id, ticket_id=0):
    return ModernKeyboards.rating_menu(message_id, ticket_id)

def get_admin_panel_keyboard():
    return AdminKeyboards.admin_main()

def get_confirm_keyboard(action, item_id, confirm_text="✅ Да", cancel_text="❌ Нет"):
    return ModernKeyboards.confirm_action(action, item_id, confirm_text, cancel_text)

def get_templates_keyboard(templates, ticket_id=None):
    return AdminKeyboards.templates_list(templates, ticket_id)

user_keyboards = ModernKeyboards()
admin_keyboards = AdminKeyboards()

__all__ = [
    "user_keyboards",
    "admin_keyboards",
    "formatter",
    "MessageFormatter",
    "get_main_menu_keyboard",
    "get_projects_keyboard",
    "get_categories_keyboard",
    "get_tickets_list_keyboard",
    "get_ticket_detail_keyboard",
    "get_ticket_actions_keyboard",
    "get_rating_keyboard",
    "get_admin_panel_keyboard",
    "get_confirm_keyboard",
    "get_templates_keyboard"
]

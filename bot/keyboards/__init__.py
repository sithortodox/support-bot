from .inline import ModernKeyboards
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
    return ModernKeyboards.ticket_menu(ticket_id, is_admin, ticket_status)

def get_rating_keyboard(message_id, ticket_id=0):
    return ModernKeyboards.rating_menu(message_id, ticket_id)

user_keyboards = ModernKeyboards()
admin_keyboards = ModernKeyboards()

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
    "get_rating_keyboard"
]

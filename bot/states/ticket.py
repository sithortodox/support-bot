from aiogram.fsm.state import State, StatesGroup

class TicketStates(StatesGroup):
    waiting_for_project = State()
    waiting_for_message = State()
    waiting_for_admin_answer = State()

class AdminStates(StatesGroup):
    waiting_for_project_name = State()
    waiting_for_project_prompt = State()
    waiting_for_broadcast = State()

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from ..keyboards import (
    get_main_menu_keyboard,
    get_projects_keyboard,
    get_ticket_actions_keyboard,
    get_tickets_list_keyboard
)
from ..states import TicketStates
from core.database.crud import Database
from core.ai.openai_client import OpenAIClient
from core.router.message_router import MessageRouter
from core.config import ADMIN_IDS, OPENAI_API_KEY, OPENAI_MODEL

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database, state: FSMContext):
    await state.clear()
    
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    if message.from_user.id in ADMIN_IDS:
        await db.set_user_role(message.from_user.id, "admin")
    
    projects = await db.get_active_projects()
    
    if projects:
        await message.answer(
            "👋 Добро пожаловать в техподдержку!\n\n"
            "Выберите проект или просто напишите ваш вопрос:",
            reply_markup=get_projects_keyboard(projects)
        )
        await state.set_state(TicketStates.waiting_for_project)
    else:
        await message.answer(
            "👋 Добро пожаловать в техподдержку!\n\n"
            "Опишите вашу проблему, и мы постараемся помочь.",
            reply_markup=get_main_menu_keyboard()
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """📚 Справка по боту техподдержки

Команды:
/start - Главное меню
/help - Эта справка
/status - Статус ваших тикетов
/operator - Вызов оператора

Как это работает:
1. Напишите ваш вопрос
2. ИИ попробует помочь
3. Если нужна помощь - напишите "оператор"

Приоритеты автоматически определяются по содержанию вопроса."""
    
    await message.answer(help_text)

@router.message(Command("status"))
async def cmd_status(message: Message, db: Database):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("Сначала напишите /start")
        return
    
    tickets = await db.get_user_tickets(user.id, limit=5)
    
    if not tickets:
        await message.answer("У вас нет открытых тикетов")
        return
    
    text = "📋 Ваши последние тикеты:\n\n"
    
    for ticket in tickets:
        status_map = {
            "open": "🟢 Открыт",
            "ai_handled": "🤖 ИИ обрабатывает",
            "human_handled": "👤 Оператор обрабатывает",
            "closed": "🔴 Закрыт"
        }
        status = status_map.get(ticket.status, ticket.status)
        text += f"#{ticket.id} - {status}\n"
        text += f"Создан: {ticket.created_at.strftime('%d.%m %H:%M')}\n\n"
    
    await message.answer(text)

@router.message(Command("operator"))
async def cmd_operator(message: Message, db: Database, state: FSMContext):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("Сначала напишите /start")
        return
    
    tickets = await db.get_user_tickets(user.id, status="open", limit=1)
    
    if tickets:
        ticket = tickets[0]
        await db.update_ticket_status(ticket.id, "human_handled")
        await message.answer(
            "✅ Ваш запрос передан оператору.\n"
            "Ожидайте ответа."
        )
    else:
        await message.answer(
            "У вас нет открытых тикетов.\n"
            "Сначала создайте вопрос через /start"
        )

@router.callback_query(F.data == "new_ticket")
async def new_ticket(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Опишите вашу проблему или вопрос:",
        reply_markup=None
    )
    await state.set_state(TicketStates.waiting_for_message)
    await callback.answer()

@router.callback_query(F.data == "my_tickets")
async def my_tickets(callback: CallbackQuery, db: Database):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Сначала напишите /start", show_alert=True)
        return
    
    tickets = await db.get_user_tickets(user.id, limit=10)
    
    if not tickets:
        await callback.answer("У вас нет тикетов", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📋 Ваши тикеты:",
        reply_markup=get_tickets_list_keyboard(tickets)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("project_"))
async def select_project(callback: CallbackQuery, db: Database, state: FSMContext):
    project_id = int(callback.data.split("_")[1])
    
    await state.update_data(project_id=project_id)
    await callback.message.edit_text(
        "📝 Опишите вашу проблему или вопрос:",
        reply_markup=None
    )
    await state.set_state(TicketStates.waiting_for_message)
    await callback.answer()

@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(callback: CallbackQuery, db: Database):
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    messages = await db.get_ticket_messages(ticket.id, limit=10)
    
    text = f"🎫 Тикет #{ticket.id}\n"
    text += f"Статус: {ticket.status}\n\n"
    text += "История:\n"
    
    for msg in messages:
        sender = "👤 Вы" if msg.sender_type == "user" else "🤖 Поддержка"
        text += f"{sender}: {msg.content[:100]}...\n"
    
    is_admin = callback.from_user.id in ADMIN_IDS
    
    await callback.message.edit_text(
        text,
        reply_markup=get_ticket_actions_keyboard(ticket.id, is_admin)
    )
    await callback.answer()

@router.message(TicketStates.waiting_for_message)
async def process_message(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()
    project_id = data.get("project_id")
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
    ticket = await db.create_ticket(
        user_id=user.id,
        project_id=project_id
    )
    
    await db.create_message(
        ticket_id=ticket.id,
        sender_type="user",
        sender_id=message.from_user.id,
        content=message.text
    )
    
    project = await db.get_project(project_id) if project_id else None
    
    if OPENAI_API_KEY:
        ai_client = OpenAIClient(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)
        router = MessageRouter(ai_client, db)
        
        priority = await router.classify_priority(message.text)
        ticket.priority = priority
        await db.session.commit()
        
        response, escalated, ai_response = await router.route(
            message=message.text,
            ticket=ticket,
            project=project
        )
        
        if ai_response:
            await db.create_ai_log(
                ticket_id=ticket.id,
                prompt_tokens=ai_response.prompt_tokens,
                completion_tokens=ai_response.completion_tokens,
                model=OPENAI_MODEL
            )
    else:
        response = "Ваш вопрос принят. Ожидайте ответа оператора."
        await db.update_ticket_status(ticket.id, "human_handled")
    
    await db.create_message(
        ticket_id=ticket.id,
        sender_type="ai" if not escalated else "system",
        content=response
    )
    
    await message.answer(
        response,
        reply_markup=get_ticket_actions_keyboard(ticket.id)
    )
    
    await state.clear()

@router.message(StateFilter(default_state))
async def handle_any_message(message: Message, db: Database, state: FSMContext):
    await state.set_state(TicketStates.waiting_for_message)
    await process_message(message, db, state)

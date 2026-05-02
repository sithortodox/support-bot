from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
import asyncio
import aiohttp
import logging

from ..keyboards import (
    get_main_menu_keyboard,
    get_projects_keyboard,
    get_ticket_actions_keyboard,
    get_tickets_list_keyboard,
    get_categories_keyboard,
    get_rating_keyboard,
    get_ticket_detail_keyboard
)
from ..states import TicketStates
from core.database.crud import Database
from core.ai.openai_client import OpenAIClient
from core.router.message_router import MessageRouter
from core.config import ADMIN_IDS, OPENAI_API_KEY, OPENAI_MODEL, BOT_TOKEN

router = Router()
logger = logging.getLogger(__name__)

async def notify_admin_new_ticket(ticket_id: int, user, message_text: str):
    text = (
        f"🔔 <b>Новый тикет #{ticket_id}</b>\n\n"
        f"👤 Пользователь: {user.first_name} (@{user.username or 'N/A'})\n"
        f"📝 Сообщение: {message_text[:200]}\n\n"
        f"Для ответа: /admin"
    )
    
    logger.info(f"Sending notification for ticket #{ticket_id} to admins: {ADMIN_IDS}")
    
    for admin_id in ADMIN_IDS:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                async with session.post(url, json={
                    "chat_id": admin_id,
                    "text": text,
                    "parse_mode": "HTML"
                }) as response:
                    if response.status == 200:
                        logger.info(f"Notification sent to admin {admin_id}")
                    else:
                        logger.error(f"Failed to send notification: {response.status} - {await response.text()}")
        except Exception as e:
            logger.error(f"Error sending notification to {admin_id}: {e}")

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
    
    categories = await db.get_ticket_categories()
    
    if categories:
        await message.answer(
            "👋 Добро пожаловать в техподдержку!\n\n"
            "Выберите категорию вопроса:",
            reply_markup=get_categories_keyboard(categories)
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
        asyncio.create_task(notify_admin_new_ticket(ticket.id, user, message.text))
        await message.answer(
            "✅ Ваш запрос передан оператору.\n"
            "Ожидайте ответа."
        )
    else:
        await message.answer(
            "У вас нет открытых тикетов.\n"
            "Сначала создайте вопрос через /start"
        )

@router.callback_query(F.data.startswith("category_"))
async def select_category(callback: CallbackQuery, db: Database, state: FSMContext):
    category_data = callback.data.split("_")[1]
    
    if category_data == "other":
        await state.update_data(category="general")
    else:
        category_id = int(category_data)
        categories = await db.get_ticket_categories()
        category = next((c for c in categories if c.id == category_id), None)
        
        if category:
            await state.update_data(category=category.name)
    
    await callback.message.edit_text(
        "📝 Опишите вашу проблему или вопрос:",
        reply_markup=None
    )
    await state.set_state(TicketStates.waiting_for_message)
    await callback.answer()

@router.callback_query(F.data.startswith("rate_positive_") | F.data.startswith("rate_negative_"))
async def rate_response(callback: CallbackQuery, db: Database):
    parts = callback.data.split("_")
    rating = parts[1]
    message_id = int(parts[2])
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    
    result = await db.session.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return
    
    await db.rate_message(
        message_id=message_id,
        user_id=user.id,
        ticket_id=message.ticket_id,
        rating=rating
    )
    
    emoji = "👍" if rating == "positive" else "👎"
    await callback.answer(f"Спасибо за оценку! {emoji}")
    
    await callback.message.edit_reply_markup(reply_markup=None)

@router.callback_query(F.data == "new_ticket")
async def new_ticket(callback: CallbackQuery, db: Database, state: FSMContext):
    categories = await db.get_ticket_categories()
    
    if categories:
        await callback.message.edit_text(
            "📁 Выберите категорию вопроса:",
            reply_markup=get_categories_keyboard(categories)
        )
    else:
        await callback.message.edit_text(
            "📝 Опишите вашу проблему или вопрос:",
            reply_markup=None
        )
        await state.set_state(TicketStates.waiting_for_message)
    await callback.answer()

from sqlalchemy import select
from core.database.models import Message

@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(callback: CallbackQuery, db: Database):
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    messages = await db.get_ticket_messages(ticket.id, limit=10)
    
    text = f"🎫 Тикет #{ticket.id}\n"
    text += f"📂 Категория: {ticket.category or 'Общее'}\n"
    text += f"⚡ Приоритет: {ticket.priority}\n"
    text += f"📊 Статус: {ticket.status}\n\n"
    text += "История:\n"
    
    last_ai_message = None
    for msg in messages:
        sender = "👤 Вы" if msg.sender_type == "user" else "🤖 Поддержка"
        text += f"{sender}: {msg.content[:100]}...\n"
        if msg.sender_type in ["ai", "admin"]:
            last_ai_message = msg
    
    is_admin = callback.from_user.id in ADMIN_IDS
    has_rating = last_ai_message.rating is not None if last_ai_message else False
    
    keyboard = get_ticket_detail_keyboard(ticket.id, is_admin, has_rating)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )
    await callback.answer()

@router.message(TicketStates.waiting_for_message)
async def process_message(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()
    project_id = data.get("project_id")
    category = data.get("category", "general")
    
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
    
    ticket.category = category
    await db.session.commit()
    
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
        
        response, escalated, ai_response = await router.route(
            message=message.text,
            ticket=ticket,
            project=project,
            user=user
        )
        
        if ai_response:
            await db.create_ai_log_with_faq(
                ticket_id=ticket.id,
                prompt_tokens=ai_response.prompt_tokens,
                completion_tokens=ai_response.completion_tokens,
                model=OPENAI_MODEL,
                used_faq=ai_response.used_faq,
                faq_id=ai_response.faq_id
            )
            
            if ai_response.sentiment:
                await db.create_sentiment_log(
                    ticket_id=ticket.id,
                    message_id=0,
                    sentiment=ai_response.sentiment.sentiment,
                    score=ai_response.sentiment.score,
                    emotions=str(ai_response.sentiment.emotions)
                )
    else:
        escalated = True
        response = "Ваш вопрос принят. Ожидайте ответа оператора."
        await db.update_ticket_status(ticket.id, "human_handled")
        asyncio.create_task(notify_admin_new_ticket(ticket.id, user, message.text))
    
    ai_message = await db.create_message(
        ticket_id=ticket.id,
        sender_type="ai" if not escalated else "system",
        content=response
    )
    
    await db.update_first_response_time(ticket.id)
    
    keyboard = get_rating_keyboard(ai_message.id)
    
    await message.answer(
        response,
        reply_markup=keyboard
    )
    
    await state.clear()

@router.message(StateFilter(default_state))
async def handle_any_message(message: Message, db: Database, state: FSMContext):
    await state.set_state(TicketStates.waiting_for_message)
    await process_message(message, db, state)

@router.message(TicketStates.waiting_for_message, F.photo)
async def handle_photo(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()
    category = data.get("category", "general")
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
    ticket = await db.create_ticket(user_id=user.id)
    ticket.category = category
    await db.session.commit()
    
    caption = message.caption or "Фото без описания"
    
    user_message = await db.create_message(
        ticket_id=ticket.id,
        sender_type="user",
        sender_id=message.from_user.id,
        content=caption,
        has_attachment=True
    )
    
    photo = message.photo[-1]
    
    await db.create_attachment(
        message_id=user_message.id,
        file_type="photo",
        file_id=photo.file_id,
        file_size=photo.file_size
    )
    
    if OPENAI_API_KEY:
        ai_client = OpenAIClient(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)
        router = MessageRouter(ai_client, db)
        
        response, escalated, ai_response = await router.route(
            message=caption,
            ticket=ticket,
            user=user
        )
    else:
        escalated = True
        response = "Ваш вопрос с вложением принят. Ожидайте ответа оператора."
        await db.update_ticket_status(ticket.id, "human_handled")
        asyncio.create_task(notify_admin_new_ticket(ticket.id, user, message.text))
    
    ai_message = await db.create_message(
        ticket_id=ticket.id,
        sender_type="ai" if not escalated else "system",
        content=response
    )
    
    await db.update_first_response_time(ticket.id)
    
    await message.answer(
        response,
        reply_markup=get_rating_keyboard(ai_message.id)
    )
    
    await state.clear()

@router.message(TicketStates.waiting_for_message, F.document)
async def handle_document(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()
    category = data.get("category", "general")
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
    ticket = await db.create_ticket(user_id=user.id)
    ticket.category = category
    await db.session.commit()
    
    caption = message.caption or f"Документ: {message.document.file_name}"
    
    user_message = await db.create_message(
        ticket_id=ticket.id,
        sender_type="user",
        sender_id=message.from_user.id,
        content=caption,
        has_attachment=True
    )
    
    await db.create_attachment(
        message_id=user_message.id,
        file_type="document",
        file_id=message.document.file_id,
        file_name=message.document.file_name,
        file_size=message.document.file_size
    )
    
    response = "Ваш документ принят. Ожидайте ответа оператора."
    await db.update_ticket_status(ticket.id, "human_handled")
    asyncio.create_task(notify_admin_new_ticket(ticket.id, user, message.text))
    
    ai_message = await db.create_message(
        ticket_id=ticket.id,
        sender_type="system",
        content=response
    )
    
    await message.answer(response)
    await state.clear()

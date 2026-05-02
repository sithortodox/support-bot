from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..keyboards import (
    get_admin_panel_keyboard,
    get_tickets_list_keyboard,
    get_ticket_actions_keyboard,
    get_confirm_keyboard
)
from ..states import AdminStates, TicketStates
from core.database.crud import Database
from core.config import ADMIN_IDS

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к админ-панели")
        return
    
    await message.answer(
        "🔧 Админ-панель",
        reply_markup=get_admin_panel_keyboard()
    )

@router.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    tickets = await db.get_open_tickets(limit=20)
    
    if not tickets:
        await callback.answer("Нет открытых тикетов", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📋 Открытые тикеты:",
        reply_markup=get_tickets_list_keyboard(tickets)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    from sqlalchemy import select, func
    from core.database.models import Ticket, User
    
    total_users = await db.session.scalar(select(func.count(User.id)))
    total_tickets = await db.session.scalar(select(func.count(Ticket.id)))
    open_tickets = await db.session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == "open")
    )
    
    text = f"""📊 Статистика

Пользователей: {total_users}
Всего тикетов: {total_tickets}
Открытых: {open_tickets}"""
    
    await callback.message.edit_text(text, reply_markup=get_admin_panel_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("answer_"))
async def admin_answer_start(callback: CallbackQuery, state: FSMContext, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer(f"💬 Напишите ответ для тикета #{ticket_id}:")
    await state.set_state(TicketStates.waiting_for_admin_answer)
    await callback.answer()

@router.message(TicketStates.waiting_for_admin_answer)
async def admin_answer_send(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    
    if not ticket_id:
        await message.answer("Ошибка: тикет не найден")
        await state.clear()
        return
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await message.answer("Тикет не найден")
        await state.clear()
        return
    
    await db.create_message(
        ticket_id=ticket.id,
        sender_type="admin",
        sender_id=message.from_user.id,
        content=message.text
    )
    
    if ticket.status == "closed":
        ticket.status = "open"
        ticket.closed_at = None
        await db.session.commit()
    
    try:
        from aiogram import Bot
        from core.config import BOT_TOKEN
        
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=ticket.user.telegram_id,
            text=f"📨 Ответ по тикету #{ticket.id}:\n\n{message.text}",
            reply_markup=get_ticket_actions_keyboard(ticket.id)
        )
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение пользователю: {e}")
    
    await message.answer("✅ Ответ отправлен")
    await state.clear()

@router.callback_query(F.data.startswith("close_"))
async def admin_close_ticket(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[1])
    
    await callback.message.edit_text(
        f"❓ Закрыть тикет #{ticket_id}?",
        reply_markup=get_confirm_keyboard("close", ticket_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_close_"))
async def confirm_close(callback: CallbackQuery, db: Database):
    ticket_id = int(callback.data.split("_")[2])
    
    ticket = await db.update_ticket_status(ticket_id, "closed")
    
    if ticket:
        await callback.message.edit_text(f"✅ Тикет #{ticket_id} закрыт")
        
        try:
            from aiogram import Bot
            from core.config import BOT_TOKEN
            
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                chat_id=ticket.user.telegram_id,
                text=f"✅ Ваш тикет #{ticket.id} закрыт"
            )
        except:
            pass
    else:
        await callback.answer("Тикет не найден", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_close_"))
async def cancel_close(callback: CallbackQuery, db: Database):
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket(ticket_id)
    
    if ticket:
        await callback.message.edit_text(
            f"🎫 Тикет #{ticket.id}",
            reply_markup=get_ticket_actions_keyboard(ticket.id, is_admin=True)
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("priority_"))
async def set_priority(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    parts = callback.data.split("_")
    ticket_id = int(parts[1])
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    priorities = ["low", "normal", "high", "urgent"]
    current_idx = priorities.index(ticket.priority) if ticket.priority in priorities else 1
    next_priority = priorities[(current_idx + 1) % len(priorities)]
    
    ticket.priority = next_priority
    await db.session.commit()
    
    await callback.answer(f"Приоритет изменен на: {next_priority}")
    
    await callback.message.edit_text(
        f"🎫 Тикет #{ticket.id}\nПриоритет: {next_priority}",
        reply_markup=get_ticket_actions_keyboard(ticket.id, is_admin=True)
    )

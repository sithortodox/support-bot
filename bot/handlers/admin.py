from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..keyboards import (
    get_admin_panel_keyboard,
    get_tickets_list_keyboard,
    get_ticket_actions_keyboard,
    get_confirm_keyboard,
    get_templates_keyboard
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

@router.message(Command("templates"))
async def cmd_templates(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    templates = await db.get_response_templates(limit=10)
    
    if not templates:
        await message.answer(
            "📝 Шаблоны не найдены.\n\n"
            "Для добавления: /template_add <название>"
        )
        return
    
    text = "📝 Шаблоны ответов:\n\n"
    
    for template in templates:
        text += f"#{template.id} {template.name}\n"
        text += f"📂 {template.category or 'Без категории'}\n"
        text += f"🎯 Использовано: {template.use_count} раз\n\n"
    
    text += "\nКоманды:\n"
    text += "/template_add <название> - добавить\n"
    text += "/template_del <id> - удалить\n"
    text += "/template_edit <id> <текст> - редактировать"
    
    await message.answer(text)

@router.message(Command("template_add"))
async def cmd_template_add(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer(
            "📝 Добавление шаблона\n\n"
            "Использование: /template_add <название>\n\n"
            "Затем отправьте текст шаблона."
        )
        await state.set_state(AdminStates.waiting_for_project_prompt)
        return
    
    template_name = parts[1]
    await state.update_data(template_name=template_name)
    await message.answer(f"Название: {template_name}\n\nОтправьте текст шаблона:")
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def process_template_content(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    template_name = data.get("template_name", "Без названия")
    
    template = await db.create_response_template(
        name=template_name,
        content=message.text,
        created_by=message.from_user.id
    )
    
    await message.answer(
        f"✅ Шаблон создан!\n\n"
        f"ID: {template.id}\n"
        f"Название: {template.name}\n"
        f"Текст: {template.content[:200]}..."
    )
    
    await state.clear()

@router.message(Command("template_del"))
async def cmd_template_del(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("Использование: /template_del <id>")
        return
    
    try:
        template_id = int(parts[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    
    from sqlalchemy import select
    from core.database.models import ResponseTemplate
    
    result = await db.session.execute(
        select(ResponseTemplate).where(ResponseTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        await message.answer("Шаблон не найден")
        return
    
    template.is_active = False
    await db.session.commit()
    
    await message.answer(f"✅ Шаблон #{template_id} удален")

@router.callback_query(F.data.startswith("templates_"))
async def show_templates(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[1])
    
    templates = await db.get_response_templates(limit=10)
    
    if not templates:
        await callback.answer("Шаблоны не найдены", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📝 Выберите шаблон:",
        reply_markup=get_templates_keyboard(templates, ticket_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("template_"))
async def use_template(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    parts = callback.data.split("_")
    template_id = int(parts[1])
    ticket_id = int(parts[2])
    
    from sqlalchemy import select
    from core.database.models import ResponseTemplate
    
    result = await db.session.execute(
        select(ResponseTemplate).where(ResponseTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        await callback.answer("Шаблон не найден", show_alert=True)
        return
    
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    await db.create_message(
        ticket_id=ticket_id,
        sender_type="admin",
        sender_id=callback.from_user.id,
        content=template.content
    )
    
    await db.increment_template_use(template_id)
    
    try:
        from aiogram import Bot
        from core.config import BOT_TOKEN
        
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=ticket.user.telegram_id,
            text=f"📨 Ответ по тикету #{ticket_id}:\n\n{template.content}"
        )
    except Exception as e:
        await callback.answer(f"Ошибка отправки: {e}", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"✅ Шаблон отправлен:\n\n{template.content[:200]}..."
    )
    await callback.answer("Сообщение отправлено!")

@router.callback_query(F.data.startswith("custom_answer_"))
async def custom_answer(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[2])
    
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer(f"💬 Напишите ответ для тикета #{ticket_id}:")
    await state.set_state(TicketStates.waiting_for_admin_answer)
    await callback.answer()

@router.message(Command("category_add"))
async def cmd_category_add(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer(
            "Использование: /category_add <название> [emoji] [приоритет]\n\n"
            "Примеры:\n"
            "/category_add technical 🔧 5\n"
            "/category_add billing 💳 4\n"
            "/category_add general 📁 1"
        )
        return
    
    name_parts = parts[1].split()
    name = name_parts[0]
    emoji = name_parts[1] if len(name_parts) > 1 else "📁"
    priority = int(name_parts[2]) if len(name_parts) > 2 else 0
    
    category = await db.create_ticket_category(
        name=name,
        emoji=emoji,
        priority=priority
    )
    
    await message.answer(
        f"✅ Категория создана!\n\n"
        f"ID: {category.id}\n"
        f"Название: {category.name}\n"
        f"Emoji: {category.emoji}\n"
        f"Приоритет: {category.priority}"
    )

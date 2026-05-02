from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database.crud import Database
from core.config import ADMIN_IDS
import logging

router = Router()
logger = logging.getLogger(__name__)

class SecurityStates(StatesGroup):
    waiting_for_block_reason = State()
    waiting_for_spam_pattern = State()
    waiting_for_setting_value = State()

@router.message(Command("block"))
async def cmd_block(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer(
            "Использование: /block <user_id> [часы] [причина]\n\n"
            "Примеры:\n"
            "/block 123456789\n"
            "/block 123456789 24 Спам\n"
            "/block 123456789 0 Вечная блокировка"
        )
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("ID пользователя должен быть числом")
        return
    
    if user_id in ADMIN_IDS:
        await message.answer("⛔ Нельзя заблокировать администратора")
        return
    
    duration_hours = None
    reason = None
    
    if len(parts) >= 3:
        try:
            duration_hours = int(parts[2])
        except ValueError:
            reason = " ".join(parts[2:])
    
    if len(parts) >= 4 and duration_hours is not None:
        reason = " ".join(parts[3:])
    
    block_type = "permanent" if duration_hours == 0 else "temporary"
    
    block = await db.block_user(
        user_id=user_id,
        blocked_by=message.from_user.id,
        reason=reason,
        block_type=block_type,
        duration_hours=duration_hours if duration_hours and duration_hours > 0 else None
    )
    
    await db.create_audit_log(
        admin_id=message.from_user.id,
        action="block_user",
        target_type="user",
        target_id=user_id,
        details=f"Reason: {reason}, Duration: {duration_hours}h, Type: {block_type}"
    )
    
    text = f"✅ Пользователь {user_id} заблокирован\n\n"
    text += f"Тип: {block_type}\n"
    if duration_hours and duration_hours > 0:
        text += f"Длительность: {duration_hours} часов\n"
    if reason:
        text += f"Причина: {reason}"
    
    await message.answer(text)
    logger.info(f"User {user_id} blocked by {message.from_user.id}")

@router.message(Command("unblock"))
async def cmd_unblock(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("Использование: /unblock <user_id>")
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("ID пользователя должен быть числом")
        return
    
    block = await db.unblock_user(user_id, message.from_user.id)
    
    if not block:
        await message.answer(f"Пользователь {user_id} не заблокирован")
        return
    
    await db.create_audit_log(
        admin_id=message.from_user.id,
        action="unblock_user",
        target_type="user",
        target_id=user_id
    )
    
    await message.answer(f"✅ Пользователь {user_id} разблокирован")
    logger.info(f"User {user_id} unblocked by {message.from_user.id}")

@router.message(Command("blocks"))
async def cmd_blocks(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    blocks = await db.get_user_blocks(active_only=True, limit=20)
    
    if not blocks:
        await message.answer("Нет активных блокировок")
        return
    
    text = "🚫 Активные блокировки:\n\n"
    
    for block in blocks:
        user = await db.get_user_by_telegram_id(block.user_id)
        username = user.username if user and user.username else block.user_id
        
        text += f"👤 {username} (ID: {block.user_id})\n"
        text += f"   Тип: {block.block_type}\n"
        if block.reason:
            text += f"   Причина: {block.reason}\n"
        if block.expires_at:
            from datetime import datetime
            remaining = block.expires_at - datetime.utcnow()
            text += f"   Осталось: {int(remaining.total_seconds() / 3600)}ч\n"
        text += "\n"
    
    await message.answer(text)

@router.message(Command("audit"))
async def cmd_audit(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    
    hours = 24
    action = None
    
    if len(parts) >= 2:
        try:
            hours = int(parts[1])
        except ValueError:
            action = parts[1]
    
    logs = await db.get_audit_logs(action=action, hours=hours, limit=50)
    
    if not logs:
        await message.answer("Логи не найдены")
        return
    
    text = f"📋 Последние действия ({hours}ч):\n\n"
    
    for log in logs[:20]:
        admin = await db.get_user_by_telegram_id(log.admin_id)
        admin_name = admin.username if admin and admin.username else log.admin_id
        
        text += f"👤 {admin_name}\n"
        text += f"   Действие: {log.action}\n"
        if log.target_type:
            text += f"   Цель: {log.target_type} #{log.target_id}\n"
        text += f"   {log.created_at.strftime('%d.%m %H:%M')}\n\n"
    
    await message.answer(text)

@router.message(Command("spam"))
async def cmd_spam(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    filters = await db.get_spam_filters(limit=20)
    
    if not filters:
        await message.answer(
            "🛡️ Фильтры спама не настроены.\n\n"
            "Добавить: /spam_add <паттерн> [действие]\n"
            "Действия: warn, block"
        )
        return
    
    text = "🛡️ Фильтры спама:\n\n"
    
    for spam_filter in filters:
        action_emoji = "⚠️" if spam_filter.action == "warn" else "🚫"
        text += f"{action_emoji} #{spam_filter.id} {spam_filter.pattern}\n"
        text += f"   Тип: {spam_filter.filter_type}\n"
        text += f"   Действие: {spam_filter.action}\n\n"
    
    text += "\nКоманды:\n"
    text += "/spam_add <паттерн> [warn|block] - добавить\n"
    text += "/spam_del <id> - удалить"
    
    await message.answer(text)

@router.message(Command("spam_add"))
async def cmd_spam_add(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 2:
        await message.answer(
            "Использование: /spam_add <паттерн> [действие]\n\n"
            "Действия:\n"
            "- warn (предупреждение)\n"
            "- block (блокировка)\n\n"
            "Примеры:\n"
            "/spam_add casino warn\n"
            "/spam_add viagra block"
        )
        return
    
    pattern = parts[1]
    action = parts[2] if len(parts) >= 3 else "warn"
    
    if action not in ["warn", "block"]:
        action = "warn"
    
    spam_filter = await db.create_spam_filter(
        pattern=pattern,
        filter_type="keyword",
        action=action,
        created_by=message.from_user.id
    )
    
    await db.create_audit_log(
        admin_id=message.from_user.id,
        action="add_spam_filter",
        target_type="spam_filter",
        target_id=spam_filter.id,
        details=f"Pattern: {pattern}, Action: {action}"
    )
    
    await message.answer(
        f"✅ Фильтр добавлен\n\n"
        f"ID: {spam_filter.id}\n"
        f"Паттерн: {pattern}\n"
        f"Действие: {action}"
    )

@router.message(Command("spam_del"))
async def cmd_spam_del(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("Использование: /spam_del <id>")
        return
    
    try:
        filter_id = int(parts[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    
    deleted = await db.delete_spam_filter(filter_id)
    
    if deleted:
        await db.create_audit_log(
            admin_id=message.from_user.id,
            action="delete_spam_filter",
            target_type="spam_filter",
            target_id=filter_id
        )
        await message.answer(f"✅ Фильтр #{filter_id} удален")
    else:
        await message.answer("Фильтр не найден")

@router.message(Command("ratelimit"))
async def cmd_ratelimit(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer(
            "Управление rate limits:\n\n"
            "/ratelimit status <user_id> - статус\n"
            "/ratelimit reset <user_id> [тип] - сброс"
        )
        return
    
    action = parts[1]
    
    if action == "status":
        if len(parts) < 3:
            await message.answer("Укажите ID пользователя")
            return
        
        user_id = int(parts[2])
        
        message_status = await db.get_rate_limit_status(user_id, "message")
        callback_status = await db.get_rate_limit_status(user_id, "callback")
        
        text = f"📊 Rate limits для {user_id}:\n\n"
        
        if message_status:
            text += f"Сообщения:\n"
            text += f"  Попыток: {message_status.attempt_count}\n"
            text += f"  Заблокирован: {'Да' if message_status.is_blocked else 'Нет'}\n\n"
        
        if callback_status:
            text += f"Кнопки:\n"
            text += f"  Попыток: {callback_status.attempt_count}\n"
            text += f"  Заблокирован: {'Да' if callback_status.is_blocked else 'Нет'}\n"
        
        if not message_status and not callback_status:
            text += "Нет записей"
        
        await message.answer(text)
    
    elif action == "reset":
        if len(parts) < 3:
            await message.answer("Укажите ID пользователя")
            return
        
        user_id = int(parts[2])
        action_type = parts[3] if len(parts) >= 4 else None
        
        if action_type:
            await db.reset_rate_limit(user_id, action_type)
        else:
            await db.reset_rate_limit(user_id, "message")
            await db.reset_rate_limit(user_id, "callback")
        
        await db.create_audit_log(
            admin_id=message.from_user.id,
            action="reset_rate_limit",
            target_type="user",
            target_id=user_id,
            details=f"Action type: {action_type or 'all'}"
        )
        
        await message.answer(f"✅ Rate limits сброшены для {user_id}")
    
    else:
        await message.answer("Неизвестное действие")

@router.message(Command("security"))
async def cmd_security(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    blocks = await db.get_user_blocks(active_only=True, limit=100)
    spam_filters = await db.get_spam_filters(limit=100)
    
    text = "🔐 Безопасность:\n\n"
    text += f"🚫 Активных блокировок: {len(blocks)}\n"
    text += f"🛡️ Фильтров спама: {len(spam_filters)}\n\n"
    text += "Команды:\n"
    text += "/block <user_id> - заблокировать\n"
    text += "/unblock <user_id> - разблокировать\n"
    text += "/blocks - список блокировок\n"
    text += "/spam - фильтры спама\n"
    text += "/spam_add - добавить фильтр\n"
    text += "/audit - логи действий\n"
    text += "/ratelimit - управление лимитами"
    
    await message.answer(text)
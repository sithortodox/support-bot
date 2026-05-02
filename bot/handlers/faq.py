from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..states import AdminStates
from core.database.crud import Database
from core.config import ADMIN_IDS

router = Router()

@router.message(Command("faq"))
async def cmd_faq(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    faqs = await db.get_all_faqs(limit=10)
    
    if not faqs:
        await message.answer(
            "📚 FAQ пуст.\n\n"
            "Для добавления используйте:\n"
            "/faq_add - добавить новый FAQ"
        )
        return
    
    text = "📚 Список FAQ:\n\n"
    
    for faq in faqs:
        text += f"#{faq.id} [{faq.language.upper()}]\n"
        text += f"❓ {faq.question[:50]}...\n"
        text += f"📂 {faq.category or 'Без категории'}\n"
        text += f"🎯 Использовано: {faq.use_count} раз\n\n"
    
    text += "\nКоманды:\n"
    text += "/faq_add - добавить\n"
    text += "/faq_search <запрос> - поиск\n"
    text += "/faq_del <id> - удалить"
    
    await message.answer(text)

@router.message(Command("faq_add"))
async def cmd_faq_add(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    await message.answer(
        "📝 Добавление нового FAQ\n\n"
        "Отправьте вопрос:"
    )
    await state.set_state(AdminStates.waiting_for_project_name)
    await state.update_data(faq_step="question")

@router.message(AdminStates.waiting_for_project_name)
async def process_faq_add(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    step = data.get("faq_step")
    
    if step == "question":
        await state.update_data(faq_question=message.text)
        await message.answer("Теперь отправьте ответ:")
        await state.update_data(faq_step="answer")
    
    elif step == "answer":
        await state.update_data(faq_answer=message.text)
        await message.answer(
            "Отправьте ключевые слова через запятую\n"
            "(для поиска) или 'пропустить':"
        )
        await state.update_data(faq_step="keywords")
    
    elif step == "keywords":
        keywords = message.text if message.text.lower() != "пропустить" else ""
        await state.update_data(faq_keywords=keywords)
        await message.answer(
            "Укажите категорию или 'пропустить':\n"
            "technical, billing, account, feature, general"
        )
        await state.update_data(faq_step="category")
    
    elif step == "category":
        category = message.text if message.text.lower() != "пропустить" else None
        await state.update_data(faq_category=category)
        await message.answer(
            "Укажите язык (ru, en) или 'ru':"
        )
        await state.update_data(faq_step="language")
    
    elif step == "language":
        language = message.text.lower() if message.text.lower() in ["ru", "en"] else "ru"
        
        faq_data = await state.get_data()
        
        faq = await db.create_faq(
            question=faq_data["faq_question"],
            answer=faq_data["faq_answer"],
            keywords=faq_data.get("faq_keywords"),
            category=faq_data.get("faq_category"),
            language=language
        )
        
        await message.answer(
            f"✅ FAQ добавлен!\n\n"
            f"ID: {faq.id}\n"
            f"Вопрос: {faq.question[:100]}"
        )
        
        await state.clear()

@router.message(Command("faq_search"))
async def cmd_faq_search(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    query = message.text.replace("/faq_search", "").strip()
    
    if not query:
        await message.answer("Использование: /faq_search <запрос>")
        return
    
    faqs = await db.search_faq(query, limit=5)
    
    if not faqs:
        await message.answer("Ничего не найдено")
        return
    
    text = "🔍 Результаты поиска:\n\n"
    
    for faq in faqs:
        text += f"#{faq.id} [{faq.language.upper()}]\n"
        text += f"❓ {faq.question}\n"
        text += f"💬 {faq.answer[:150]}...\n\n"
    
    await message.answer(text)

@router.message(Command("faq_del"))
async def cmd_faq_del(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    try:
        faq_id = int(message.text.replace("/faq_del", "").strip())
    except ValueError:
        await message.answer("Использование: /faq_del <id>")
        return
    
    faq = await db.get_faq(faq_id)
    
    if not faq:
        await message.answer("FAQ не найден")
        return
    
    faq.is_active = False
    await db.session.commit()
    
    await message.answer(f"✅ FAQ #{faq_id} удален")

@router.message(Command("faq_edit"))
async def cmd_faq_edit(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    await message.answer(
        "📝 Редактирование FAQ\n\n"
        "Использование:\n"
        "/faq_edit <id> question <новый вопрос>\n"
        "/faq_edit <id> answer <новый ответ>\n"
        "/faq_edit <id> category <категория>\n"
        "/faq_edit <id> priority <число>"
    )

@router.message(F.text.startswith("/faq_edit"))
async def process_faq_edit(message: Message, db: Database):
    parts = message.text.split(maxsplit=3)
    
    if len(parts) < 4:
        await message.answer("Неверный формат. Пример: /faq_edit 1 answer Новый ответ")
        return
    
    try:
        faq_id = int(parts[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    
    field = parts[2].lower()
    value = parts[3]
    
    faq = await db.get_faq(faq_id)
    
    if not faq:
        await message.answer("FAQ не найден")
        return
    
    if field == "question":
        faq.question = value
    elif field == "answer":
        faq.answer = value
    elif field == "category":
        faq.category = value
    elif field == "priority":
        try:
            faq.priority = int(value)
        except ValueError:
            await message.answer("Приоритет должен быть числом")
            return
    else:
        await message.answer(f"Неизвестное поле: {field}")
        return
    
    await db.session.commit()
    await message.answer(f"✅ FAQ #{faq_id} обновлен")

@router.message(Command("faq_import"))
async def cmd_faq_import(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    await message.answer(
        "📥 Импорт FAQ\n\n"
        "Отправьте JSON массив:\n"
        "```json\n"
        '[\n'
        '  {"question": "...", "answer": "...", "keywords": "...", "category": "...", "language": "ru"},\n'
        '  ...\n'
        ']\n'
        "```\n\n"
        "Или отправьте файл .json"
    )

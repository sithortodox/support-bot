from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core.database.crud import Database
from core.config import ADMIN_IDS
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    hours = 24
    
    if len(parts) >= 2:
        try:
            hours = int(parts[1])
        except ValueError:
            pass
    
    ticket_stats = await db.get_ticket_stats(hours=hours)
    ai_stats = await db.get_ai_stats(hours=hours)
    satisfaction = await db.get_satisfaction_stats(hours=hours)
    
    text = f"📊 Статистика за {hours}ч\n\n"
    
    text += "🎫 Тикеты:\n"
    text += f"  Всего: {ticket_stats['total_tickets']}\n"
    text += f"  Открытых: {ticket_stats['open_tickets']}\n"
    text += f"  Закрытых: {ticket_stats['closed_tickets']}\n"
    
    if ticket_stats['avg_response_time_minutes']:
        text += f"  Ср. время ответа: {ticket_stats['avg_response_time_minutes']:.1f} мин\n"
    
    text += "\n🤖 AI:\n"
    text += f"  Запросов: {ai_stats['total_requests']}\n"
    text += f"  Токенов: {ai_stats['total_tokens']:,}\n"
    text += f"  Стоимость: ${ai_stats['estimated_cost']:.4f}\n"
    
    if ai_stats['avg_response_time']:
        text += f"  Ср. время: {ai_stats['avg_response_time']:.2f}с\n"
    
    text += f"  FAQ использовано: {ai_stats['faq_usage_rate']:.1f}%\n"
    
    text += "\n⭐ Удовлетворенность:\n"
    text += f"  Оценок: {satisfaction['total_ratings']}\n"
    text += f"  👍 {satisfaction['positive']}\n"
    text += f"  👎 {satisfaction['negative']}\n"
    
    if satisfaction['satisfaction_rate']:
        text += f"  Рейтинг: {satisfaction['satisfaction_rate']:.1f}%\n"
    
    await message.answer(text)

@router.message(Command("report"))
async def cmd_report(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    days = 7
    parts = message.text.split()
    
    if len(parts) >= 2:
        try:
            days = int(parts[1])
        except ValueError:
            pass
    
    hours = days * 24
    
    ticket_stats = await db.get_ticket_stats(hours=hours)
    ai_stats = await db.get_ai_stats(hours=hours)
    satisfaction = await db.get_satisfaction_stats(hours=hours)
    categories = await db.get_category_distribution(hours=hours)
    sentiment = await db.get_sentiment_distribution(hours=hours)
    
    text = f"📈 Отчет за {days} дней\n\n"
    
    text += "════════════════════\n"
    text += "🎫 ТИКЕТЫ\n"
    text += "════════════════════\n"
    text += f"Создано: {ticket_stats['total_tickets']}\n"
    text += f"Закрыто: {ticket_stats['closed_tickets']}\n"
    
    if ticket_stats['avg_response_time_minutes']:
        hours_resp = ticket_stats['avg_response_time_minutes'] / 60
        text += f"Ср. время ответа: {hours_resp:.1f}ч\n"
    
    text += "\n════════════════════\n"
    text += "🤖 AI МЕТРИКИ\n"
    text += "════════════════════\n"
    text += f"Обработано запросов: {ai_stats['total_requests']}\n"
    text += f"Использовано токенов: {ai_stats['total_tokens']:,}\n"
    text += f"Оценочная стоимость: ${ai_stats['estimated_cost']:.2f}\n"
    text += f"FAQ命中率: {ai_stats['faq_usage_rate']:.1f}%\n"
    
    text += "\n════════════════════\n"
    text += "⭐ УДОВЛЕТВОРЕННОСТЬ\n"
    text += "════════════════════\n"
    
    if satisfaction['total_ratings'] > 0:
        text += f"Всего оценок: {satisfaction['total_ratings']}\n"
        text += f"Положительных: {satisfaction['positive']}\n"
        text += f"Отрицательных: {satisfaction['negative']}\n"
        
        if satisfaction['satisfaction_rate']:
            text += f"Уровень удовлетворенности: {satisfaction['satisfaction_rate']:.1f}%\n"
    else:
        text += "Нет оценок за период\n"
    
    if categories['categories']:
        text += "\n════════════════════\n"
        text += "📂 ПО КАТЕГОРИЯМ\n"
        text += "════════════════════\n"
        
        sorted_cats = sorted(
            categories['categories'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for cat, count in sorted_cats:
            percentage = (count / categories['total'] * 100) if categories['total'] > 0 else 0
            text += f"{cat}: {count} ({percentage:.1f}%)\n"
    
    if sentiment:
        text += "\n════════════════════\n"
        text += "😊 СЕНТИМЕНТ\n"
        text += "════════════════════\n"
        
        for s_name, s_data in list(sentiment.items())[:5]:
            text += f"{s_name}: {s_data['count']}\n"
    
    await message.answer(text)

@router.message(Command("cost"))
async def cmd_cost(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    parts = message.text.split()
    days = 30
    
    if len(parts) >= 2:
        try:
            days = int(parts[1])
        except ValueError:
            pass
    
    hours = days * 24
    
    ai_stats = await db.get_ai_stats(hours=hours)
    
    daily_cost = ai_stats['estimated_cost'] / days if days > 0 else 0
    monthly_cost = daily_cost * 30
    
    text = f"💰 Расчет стоимости OpenAI\n\n"
    text += f"Период: {days} дней\n\n"
    text += f"Запросов: {ai_stats['total_requests']}\n"
    text += f"Токенов: {ai_stats['total_tokens']:,}\n"
    text += f"  - Prompt: {ai_stats['prompt_tokens']:,}\n"
    text += f"  - Completion: {ai_stats['completion_tokens']:,}\n\n"
    text += f"Стоимость за период: ${ai_stats['estimated_cost']:.2f}\n"
    text += f"В день: ${daily_cost:.2f}\n"
    text += f"В месяц (прогноз): ${monthly_cost:.2f}\n\n"
    text += f"Тариф: GPT-4\n"
    text += f"  Prompt: $0.03/1K tokens\n"
    text += f"  Completion: $0.06/1K tokens"
    
    await message.answer(text)

@router.message(Command("activity"))
async def cmd_activity(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    hours = 168
    
    activity = await db.get_hourly_activity(hours=hours)
    
    if not activity:
        await message.answer("Нет данных об активности")
        return
    
    max_count = max(a['count'] for a in activity)
    
    text = "📊 Активность по часам (UTC)\n\n"
    
    chart_lines = []
    for hour in range(24):
        hour_data = next((a for a in activity if a['hour'] == hour), None)
        count = hour_data['count'] if hour_data else 0
        
        bar_length = int((count / max_count) * 20) if max_count > 0 else 0
        bar = "█" * bar_length + "░" * (20 - bar_length)
        
        chart_lines.append(f"{hour:02d}:00 │{bar}│ {count}")
    
    text += "```\n"
    text += "\n".join(chart_lines[:12])
    text += "\n```\n\n"
    text += "Данные за последние 7 дней"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("export"))
async def cmd_export(message: Message, db: Database):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    await message.answer(
        "📥 Экспорт данных\n\n"
        "Доступно через API:\n"
        "GET /api/v1/analytics/export/tickets\n\n"
        "Параметры:\n"
        "- project_id (опционально)\n"
        "- hours (по умолчанию 720)\n\n"
        "Возвращает CSV файл"
    )

@router.message(Command("dashboard"))
async def cmd_dashboard(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return
    
    text = "📊 Dashboard доступен через API:\n\n"
    text += "GET /api/v1/analytics/dashboard\n\n"
    text += "Параметры:\n"
    text += "- project_id (опционально)\n"
    text += "- hours (по умолчанию 24)\n\n"
    text += "Возвращает JSON с:\n"
    text += "- AI метрики\n"
    text += "- Удовлетворенность\n"
    text += "- Распределение по категориям\n"
    text += "- Сентимент\n"
    text += "- Активность по часам\n"
    text += "- Статистика тикетов"
    
    await message.answer(text)
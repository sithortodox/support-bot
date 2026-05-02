# Support Bot - Универсальный ТГ-бот техподдержки

Бот техподдержки с интеграцией OpenAI и возможностью ответа администраторов.

## Возможности

- 🤖 Автоматические ответы через OpenAI (GPT-4/GPT-3.5)
- 👥 Ручная обработка администраторами
- 🔄 Автоматическая маршрутизация (ИИ → оператор)
- 📊 Система приоритетов тикетов
- 🏗️ Поддержка нескольких проектов
- 📈 REST API для интеграций

## Быстрый старт

```bash
# Клонируйте репозиторий
cd support-bot

# Скопируйте .env.example в .env и заполните переменные
cp .env.example .env

# Запустите через Docker
docker-compose up -d
```

## Переменные окружения

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `OPENAI_API_KEY` | API ключ OpenAI | ❌ (без ИИ) |
| `DATABASE_URL` | URL PostgreSQL | ✅ |
| `REDIS_URL` | URL Redis | ✅ |
| `ADMIN_IDS` | ID администраторов через запятую | ✅ |
| `WEBHOOK_URL` | URL для webhook (опционально) | ❌ |

## Режимы работы

### Polling (по умолчанию)
Без указания `WEBHOOK_URL` бот работает в режиме long polling.

### Webhook
Укажите `WEBHOOK_URL=https://your-domain.com/webhook` для работы через webhook.

## API Endpoints

- `GET /` - Статус сервиса
- `GET /health` - Health check
- `POST /webhook/{token}` - Telegram webhook
- `GET /admin/tickets` - Список тикетов
- `POST /admin/message` - Отправить сообщение
- `GET /admin/stats` - Статистика

## Команды бота

### Пользователи
- `/start` - Главное меню
- `/help` - Справка
- `/status` - Статус тикетов
- `/operator` - Вызов оператора

### Администраторы
- `/admin` - Админ-панель
- `/tickets` - Открытые тикеты

## Структура проекта

```
support-bot/
├── bot/              # Обработчики бота
├── core/             # Бизнес-логика
│   ├── ai/           # OpenAI клиент
│   ├── database/     # Модели БД
│   └── router/       # Маршрутизация
├── api/              # REST API
├── config.py         # Конфигурация
└── main.py           # Точка входа
```

## Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск локально
python main.py
```

## Лицензия

MIT

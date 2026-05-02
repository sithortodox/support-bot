# Support Bot - Универсальный ТГ-бот техподдержки

Бот техподдержки с расширенной интеграцией OpenAI и возможностью ответа администраторов.

## Возможности

### 🤖 AI и маршрутизация
- **Sentiment Analysis** - автоматическое определение эмоционального тона сообщений
- **Контекстные промпты** - персонализированные ответы на основе истории пользователя
- **Мультиязычность** - автоопределение языка (ru/en) и ответы на соответствующем языке
- **Категоризация** - автоматическое определение категории (technical, billing, account, feature, general)
- **FAQ интеграция** - база знаний с поиском и приоритизацией
- **Кэширование** - сохранение ответов на похожие вопросы

### 👥 Поддержка
- 🔄 Автоматическая маршрутизация (ИИ → оператор)
- 📊 Умная система приоритетов на основе sentiment и категории
- 🏗️ Поддержка нескольких проектов
- 📈 REST API для интеграций

### 🎨 Современный UI/UX
- **Интуитивное меню** - удобная навигация для пользователей
- **Админ-панель** - полнофункциональная панель управления
- **Визуальные карточки** - красиво оформленная информация
- **Индикаторы статуса** - цветовое кодирование приоритетов
- **Breadcrumb навигация** - легкий возврат к предыдущим экранам
- **Emoji-иконки** - визуальное отличие категорий и действий

## Быстрый старт

```bash
# Клонируйте репозиторий
git clone https://github.com/sithortodox/support-bot.git
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
| `OPENAI_MODEL` | Модель (gpt-4/gpt-3.5-turbo) | ❌ |
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
- `GET /health` - Health check (БД, Redis, OpenAI)
- `GET /ready` - Kubernetes readiness probe
- `GET /live` - Kubernetes liveness probe
- `GET /metrics` - Prometheus metrics
- `POST /webhook/{token}` - Telegram webhook
- `GET /admin/tickets` - Список тикетов
- `POST /admin/message` - Отправить сообщение
- `GET /admin/stats` - Статистика
- `GET /dashboard` - HTML Dashboard

### Analytics API
- `GET /api/v1/analytics/ai` - AI метрики
- `GET /api/v1/analytics/satisfaction` - Удовлетворенность
- `GET /api/v1/analytics/categories` - По категориям
- `GET /api/v1/analytics/sentiment` - Сентимент
- `GET /api/v1/analytics/activity` - Активность по часам
- `GET /api/v1/analytics/history` - История агрегаций
- `GET /api/v1/analytics/export/tickets` - Экспорт CSV
- `GET /api/v1/analytics/dashboard` - Все данные
- `POST /api/v1/analytics/aggregate` - Триггер агрегации

## Команды бота

### Пользователи
- `/start` - Главное меню
- `/help` - Справка
- `/status` - Статус тикетов
- `/operator` - Вызов оператора

### Администраторы
- `/admin` - Админ-панель
- `/tickets` - Открытые тикеты
- `/faq` - Список FAQ
- `/faq_add` - Добавить FAQ
- `/faq_search <query>` - Поиск по FAQ
- `/faq_del <id>` - Удалить FAQ
- `/faq_edit <id> <field> <value>` - Редактировать FAQ
- `/templates` - Шаблоны ответов
- `/template_add <название>` - Добавить шаблон
- `/template_del <id>` - Удалить шаблон
- `/category_add <название> [emoji] [приоритет]` - Добавить категорию
- `/security` - Панель безопасности
- `/stats [hours]` - Быстрая статистика
- `/report [days]` - Детальный отчет
- `/cost [days]` - Расчет стоимости OpenAI
- `/activity` - График активности
- `/export` - Экспорт данных
- `/dashboard` - Информация о dashboard
- `/block <user_id> [часы] [причина]` - Заблокировать пользователя
- `/unblock <user_id>` - Разблокировать
- `/blocks` - Список блокировок
- `/audit [часы]` - Логи действий админов
- `/spam` - Фильтры спама
- `/spam_add <паттерн> [warn|block]` - Добавить фильтр
- `/spam_del <id>` - Удалить фильтр
- `/ratelimit status|reset <user_id>` - Управление лимитами

## AI Features详解

### Sentiment Analysis
Автоматически анализирует эмоциональный тон каждого сообщения:
- **positive/negative/neutral/frustrated/angry**
- Оценка от 0 (очень негативный) до 1 (очень позитивный)
- Эмоции: frustration, anger, urgency, satisfaction

При сильном негативе (`score < 0.2`) автоматически эскалирует оператору.

### Контекст пользователя
Отслеживает для каждого пользователя:
- Последние темы обсуждения
- Предпочитаемый язык
- Средний sentiment
- Количество сообщений

Использует это для персонализации ответов.

### Категоризация
Автоматически определяет тип вопроса:
- `technical` - баги, ошибки, системные сбои
- `billing` - платежи, подписки, возвраты
- `account` - вход, пароли, профиль
- `feature` - запросы функций
- `general` - общие вопросы

### FAQ System
База знаний с приоритизацией:
- Поиск по ключевым словам
- Поддержка категорий и языков
- Счётчик использований
- Интеграция в ответы ИИ

## User Experience

### Категории вопросов
При старте пользователю предлагается выбрать категорию:
- 🔧 Technical - технические проблемы
- 💳 Billing - вопросы оплаты
- 👤 Account - проблемы с аккаунтом
- 💡 Feature - запросы функций
- 📁 General - общие вопросы

### Рейтинг ответов
После каждого ответа ИИ пользователь может оценить:
- 👍 **Полезно** - положительная оценка
- 👎 **Не помогло** - отрицательная оценка

Рейтинги используются для:
- Подсчета satisfaction rate
- Улучшения качества ответов
- Аналитики эффективности ИИ

### Вложения
Пользователи могут отправлять:
- 📷 **Фото** - скриншоты проблем
- 📄 **Документы** - логи, файлы

Вложения сохраняются в БД и доступны админам.

### ETA (Ожидаемое время ответа)
Автоматический расчет:
- Среднее время первого ответа
- Статистика по проектам
- Мониторинг SLA

## Структура проекта

```
support-bot/
├── bot/              # Обработчики бота
│   ├── handlers/     # Пользователи, админы, FAQ
│   ├── keyboards/    # Inline-клавиатуры
│   ├── middlewares/  # БД и авторизация
│   └── states/       # FSM состояния
├── core/             # Бизнес-логика
│   ├── ai/           # OpenAI клиент + sentiment
│   ├── database/     # Модели БД + CRUD
│   └── router/       # Маршрутизация сообщений
├── api/              # REST API
├── config.py         # Конфигурация
└── main.py           # Точка входа
```

## База данных

### Модели
- **User** - пользователи с языком и статистикой
- **Project** - проекты с кастомными промптами
- **Ticket** - тикеты с sentiment, категорией, языком, response_time
- **Message** - сообщения с рейтингом и вложениями
- **FAQ** - база знаний
- **UserContext** - контекст пользователя
- **SentimentLog** - логи сентимента
- **AILog** - логи AI с использованием FAQ
- **Attachment** - вложения (фото, документы)
- **ResponseTemplate** - шаблоны ответов админов
- **RatingLog** - логи рейтингов пользователей
- **TicketCategory** - категории тикетов
- **UserBlock** - блокировки пользователей
- **AuditLog** - логи действий админов
- **RateLimitLog** - логи rate limiting
- **SpamFilter** - фильтры спама
- **SecuritySettings** - настройки безопасности
- **AnalyticsAggregation** - агрегация метрик по дням

## Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Установка dev зависимостей (тесты, линтинг)
pip install -r requirements-dev.txt

# Запуск локально
python main.py

# Запуск тестов
make test
# или
pytest --cov=. --cov-report=html -v

# Быстрые тесты
make test-fast

# Линтинг
make lint

# Форматирование кода
make format

# Очистка кэша
make clean

# Coverage отчет
make coverage
```

## Тестирование

### Unit тесты
- **Модели БД** - все 18 моделей протестированы
- **CRUD операции** - User, Ticket, Message, FAQ, Security, Analytics
- **OpenAI клиент** - mocked тесты для всех методов
- **Router** - тестирование маршрутизации и эскалации

### Integration тесты
- API endpoints
- Analytics endpoints
- Dashboard
- Export функционал

### Coverage
- Минимальный порог: 50%
- HTML отчеты в `htmlcov/`
- Загрузка в Codecov

### CI/CD Pipeline
GitHub Actions автоматически:
- ✅ Запускает тесты на Python 3.11, 3.12
- ✅ Проверяет код Ruff линтером
- ✅ Форматирует Black
- ✅ Генерирует coverage отчет
- ✅ Загружает в Codecov
- ✅ Сканирует на уязвимости Trivy
- ✅ Собирает Docker образ

### Makefile команды
```
make install       - Установка зависимостей
make test          - Тесты с coverage
make test-fast     - Быстрые тесты
make lint          - Проверка кода
make format        - Форматирование
make clean         - Очистка кэша
make docker-up     - Запуск Docker
make docker-down   - Остановка Docker
make migrate       - Миграции БД
make coverage      - Coverage отчет
make check         - Все проверки
```

## Тестирование

## Примеры использования

### Добавление FAQ через бота
```
/faq_add
→ Вопрос: Как сменить пароль?
→ Ответ: Перейдите в Настройки → Безопасность → Сменить пароль
→ Ключевые слова: пароль, сменить, безопасность
→ Категория: account
→ Язык: ru
```

### Автоматическая эскалация
Бот автоматически передаст оператору если:
- Пользователь написал "оператор" или подобное
- Sentiment score < 0.2 (сильное разочарование)
- Категория urgent (критические проблемы)
- ИИ не уверен в ответе (confidence < 0.6)

## Безопасность

### Rate Limiting
Защита от злоупотреблений:
- **Сообщения**: 20 в минуту
- **Кнопки**: 30 в минуту
- **Тикеты**: 5 за 5 минут

При превышении лимита пользователь временно блокируется.

### Блокировка пользователей
Админы могут блокировать пользователей:
```
/block 123456789 24 Спам сообщений
/block 123456789 0 Нарушение правил (вечная)
/unblock 123456789
```

Типы блокировок:
- **temporary** - временная (с длительностью)
- **permanent** - вечная
- **spam** - за спам (автоматически)

### Анти-спам
Фильтрация спама по ключевым словам:
```
/spam_add casino warn    # Предупреждение
/spam_add viagra block   # Автоблокировка
```

### Audit Logs
Все действия админов логируются:
```
/audit         # За последние 24 часа
/audit 72      # За 72 часа
/audit block   # Только блокировки
```

### Команды безопасности
```
/security              # Панель безопасности
/block <id> [h] [reason]  # Заблокировать
/unblock <id>          # Разблокировать
/blocks                # Активные блокировки
/audit [hours]         # Логи действий
/spam                  # Фильтры спама
/spam_add <p> [action] # Добавить фильтр
/spam_del <id>         # Удалить фильтр
/ratelimit status <id> # Статус лимитов
/ratelimit reset <id>  # Сброс лимитов
```

## Аналитика

### Dashboard
Визуальный дашборд доступен на `/dashboard`:
- AI метрики (токены, стоимость, время ответа)
- Удовлетворенность пользователей
- Распределение по категориям
- Сентимент анализ
- Активность по часам
- Автообновление каждую минуту

### AI Метрики
Отслеживание эффективности ИИ:
- **Токены**: prompt, completion, total
- **Стоимость**: расчет по тарифам GPT-4
- **Время ответа**: среднее время генерации
- **FAQ использование**: процент ответов из базы знаний

### Команды статистики
```
/stats [hours]       # Быстрая статистика
/report [days]       # Детальный отчет
/cost [days]         # Анализ расходов OpenAI
/activity            # График активности по часам
/export              # Инструкция по экспорту
/dashboard           # Ссылка на web dashboard
```

### Экспорт данных
CSV экспорт через API:
```
GET /api/v1/analytics/export/tickets?hours=720
```

Параметры:
- `project_id` (опционально) - фильтр по проекту
- `hours` (по умолчанию 720) - период в часах

### Шаблоны ответов
Админы могут создавать шаблоны для быстрых ответов:
```
/templates - список шаблонов
/template_add <название> - создать шаблон
```

При ответе на тикет можно выбрать шаблон из списка или написать свой текст.

### Категории тикетов
Управление категориями:
```
/category_add technical 🔧 5
/category_add billing 💳 4
/category_add general 📁 1
```

Параметры:
- name - название категории
- emoji - эмодзи для отображения
- priority - приоритет (влияет на порядок отображения)

## Мониторинг

### Prometheus Metrics
Доступны на `GET /metrics`:
- **Bot metrics** - сообщения, тикеты, рейтинги
- **AI metrics** - запросы, токены, стоимость, время ответа
- **HTTP metrics** - запросы, время ответа
- **Database metrics** - подключения

### Health Checks
```bash
# Полная проверка
curl http://localhost:8000/health

# Kubernetes probes
curl http://localhost:8000/ready  # readiness
curl http://localhost:8000/live   # liveness
```

### Логирование
- `logs/support_bot.log` - все логи
- `logs/errors.log` - только ошибки
- `logs/ai.log` - AI логи

Ротация: 10MB, 5 backups

### Миграции БД (Alembic)
```bash
# Применить миграции
alembic upgrade head

# Создать миграцию
alembic revision --autogenerate -m "description"

# Откатить
alembic downgrade -1
```

### Alerting
Пороги алертов:
- Response time > 5s
- Error rate > 10%
- Open tickets > 100
- AI cost > $10/day
- Negative sentiment < 0.3

### Grafana Dashboard
Примеры панелей:
- Request rate
- Error rate
- Response time (p95)
- Open tickets
- AI cost
- User satisfaction

Подробная документация: [docs/MONITORING.md](docs/MONITORING.md)

## Лицензия

MIT

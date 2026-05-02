# Support Bot - Production Deployment Guide

## 📋 Предварительные требования

- VPS сервер (Ubuntu 20.04/22.04)
- Минимум 2GB RAM, 2 CPU
- Домен (опционально для SSL)
- Telegram Bot Token
- OpenAI API Key

## 🚀 Быстрый деплой (рекомендуется)

### 1. Подключение к серверу
```bash
ssh root@138.124.181.35
# Пароль: sn6n9n3aVkVso4y
```

### 2. Запуск скрипта установки
```bash
# Скачайте и запустите скрипт
curl -fsSL https://raw.githubusercontent.com/sithortodox/support-bot/main/deploy/deploy.sh | bash

# Или вручную:
wget https://raw.githubusercontent.com/sithortodox/support-bot/main/deploy/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

### 3. Настройка переменных окружения
```bash
cd /opt/support-bot
nano .env
```

Измените:
- `BOT_TOKEN` - токен вашего Telegram бота
- `OPENAI_API_KEY` - ваш OpenAI API ключ
- `ADMIN_IDS` - ваш Telegram ID (узнать: @userinfobot)
- `WEBHOOK_URL` - https://your-domain.com/webhook (если есть домен)

### 4. Запуск бота
```bash
systemctl start support-bot
systemctl status support-bot
```

### 5. Проверка логов
```bash
docker-compose logs -f
```

## 🌐 Настройка домена и SSL (опционально)

### 1. Укажите A-запись домена
```
Type: A
Name: @
Value: 138.124.181.35
```

### 2. Получите SSL сертификат
```bash
certbot --nginx -d your-domain.com
```

### 3. Обновите .env
```bash
nano /opt/support-bot/.env
# Измените WEBHOOK_URL=https://your-domain.com/webhook
```

### 4. Перезапустите бота
```bash
systemctl restart support-bot
```

## 🔧 Управление ботом

### Systemd команды
```bash
# Запуск
systemctl start support-bot

# Остановка
systemctl stop support-bot

# Перезапуск
systemctl restart support-bot

# Статус
systemctl status support-bot

# Логи systemd
journalctl -u support-bot -f
```

### Docker команды
```bash
cd /opt/support-bot

# Просмотр логов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f bot
docker-compose logs -f postgres

# Статус контейнеров
docker-compose ps

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Запуск
docker-compose up -d

# Пересборка
docker-compose up -d --build
```

## 📊 Мониторинг

### Health checks
```bash
# Health check
curl http://localhost:8000/health

# Readiness
curl http://localhost:8000/ready

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Просмотр логов
```bash
# Все логи
tail -f /opt/support-bot/logs/support_bot.log

# Ошибки
tail -f /opt/support-bot/logs/errors.log

# AI логи
tail -f /opt/support-bot/logs/ai.log
```

### Мониторинг ресурсов
```bash
# CPU и память
htop

# Docker статистика
docker stats

# Диск
df -h

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## 🔒 Безопасность

### Firewall (UFW)
```bash
# Статус
ufw status

# Открыть порт
ufw allow 8080

# Закрыть порт
ufw deny 8080

# Отключить firewall (не рекомендуется)
ufw disable
```

### Fail2ban
```bash
# Статус
fail2ban-client status

# Разблокировать IP
fail2ban-client set sshd unbanip IP_ADDRESS

# Посмотреть заблокированные
fail2ban-client status sshd
```

### Обновление системы
```bash
apt update && apt upgrade -y
```

## 🔄 Обновление бота

### Автоматическое обновление
```bash
cd /opt/support-bot
git pull
docker-compose down
docker-compose up -d --build
```

### Обновление с миграциями
```bash
cd /opt/support-bot
git pull
docker-compose run bot alembic upgrade head
docker-compose restart bot
```

## 🗄️ Резервное копирование

### Бэкап базы данных
```bash
# Создать бэкап
docker-compose exec postgres pg_dump -U postgres support_bot > backup_$(date +%Y%m%d).sql

# Восстановить
cat backup_20240115.sql | docker-compose exec -T postgres psql -U postgres support_bot
```

### Автоматические бэкапы (cron)
```bash
crontab -e

# Добавить строку (бэкап каждый день в 2:00)
0 2 * * * cd /opt/support-bot && docker-compose exec -T postgres pg_dump -U postgres support_bot > /backup/db_$(date +\%Y\%m\%d).sql
```

## 🐛 Устранение проблем

### Бот не запускается
```bash
# Проверить логи
docker-compose logs bot

# Проверить .env
cat .env

# Пересобрать
docker-compose down
docker-compose up -d --build
```

### Ошибка подключения к БД
```bash
# Проверить контейнер postgres
docker-compose ps postgres

# Перезапустить postgres
docker-compose restart postgres

# Проверить логи postgres
docker-compose logs postgres
```

### Webhook не работает
```bash
# Удалить webhook
curl -F "url=" https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook

# Установить заново
curl -F "url=https://your-domain.com/webhook/<YOUR_TOKEN>" https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook

# Проверить
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

### Nginx ошибки
```bash
# Проверить конфигурацию
nginx -t

# Перезапустить
systemctl restart nginx

# Логи
tail -f /var/log/nginx/error.log
```

## 📱 Доступ к API

После запуска доступны:
- **Health**: http://138.124.181.35/health
- **Metrics**: http://138.124.181.35/metrics
- **Dashboard**: http://138.124.181.35/dashboard
- **API**: http://138.124.181.35/api/v1/analytics/...

## 🎯 Рекомендации по производительности

### Настройка Docker
```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

systemctl restart docker
```

### Оптимизация PostgreSQL
Уже настроено в docker-compose.yml, но можно увеличить:
- `SHARED_BUFFERS`
- `MAX_CONNECTIONS`

## 📞 Поддержка

- **GitHub**: https://github.com/sithortodox/support-bot
- **Issues**: https://github.com/sithortodox/support-bot/issues
- **Logs**: `/opt/support-bot/logs/`

## 🎉 После деплоя

1. Проверьте бота в Telegram: `/start`
2. Отправьте тестовый вопрос
3. Проверьте админ-панель: `/admin`
4. Настройте FAQ: `/faq_add`
5. Добавьте шаблоны: `/template_add`

Удачи! 🚀

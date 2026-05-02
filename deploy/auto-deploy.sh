#!/bin/bash
# Support Bot Automatic Deployment
# Все данные уже настроены - просто запустите этот скрипт

set -e

BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
ADMIN_IDS="YOUR_TELEGRAM_ID"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
DOMAIN="your-domain.com"

echo "╔════════════════════════════════════╗"
echo "║  Support Bot Auto-Deploy            ║"
echo "║  Domain: $DOMAIN    ║"
echo "╚════════════════════════════════════╝"

# Update system
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Install packages
echo "📦 Установка пакетов..."
apt install -y \
    curl \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    fail2ban \
    htop \
    tmux

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create directory
echo "📁 Создание директории..."
mkdir -p /opt/support-bot
cd /opt/support-bot

# Clone repository
echo "📥 Клонирование репозитория..."
rm -rf .git .env
git clone https://github.com/sithortodox/support-bot.git .
git checkout main

# Create .env with your data
echo "⚙️ Создание .env файла..."
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
WEBHOOK_URL=https://$DOMAIN/webhook
WEBHOOK_SECRET=$(openssl rand -hex 32)
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_MODEL=gpt-4o
DATABASE_URL=postgresql://postgres:\${POSTGRES_PASSWORD}@postgres:5432/support_bot
REDIS_URL=redis://redis:6379/0
ADMIN_IDS=$ADMIN_IDS
POSTGRES_PASSWORD=\${POSTGRES_PASSWORD:-change_me_in_production}
LOG_LEVEL=INFO
EOF

# Configure Nginx
echo "🌐 Настройка Nginx..."
cat > /etc/nginx/sites-available/support-bot << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /metrics {
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /dashboard {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

ln -sf /etc/nginx/sites-available/support-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Configure Firewall
echo "🔥 Настройка firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Configure Fail2ban
echo "🔒 Настройка fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Create systemd service
echo "🔧 Создание systemd сервиса..."
cat > /etc/systemd/system/support-bot.service << 'EOF'
[Unit]
Description=Support Bot
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/support-bot
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable support-bot

# Get SSL Certificate
echo "📜 Получение SSL сертификата..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect

# Setup auto-renewal
echo "🔄 Настройка автообновления SSL..."
systemctl enable certbot-renew.timer
systemctl start certbot-renew.timer

# Pull Docker images
echo "📦 Загрузка Docker образов..."
docker-compose pull

# Start the bot
echo "🚀 Запуск бота..."
docker-compose up -d

# Wait for services
echo "⏳ Ожидание запуска сервисов..."
sleep 15

# Check status
echo "✅ Проверка статуса..."
docker-compose ps

# Set webhook
echo "🔗 Установка webhook..."
curl -s -F "url=https://$DOMAIN/webhook/$BOT_TOKEN" \
    -F "secret_token=$(grep WEBHOOK_SECRET .env | cut -d= -f2)" \
    https://api.telegram.org/bot$BOT_TOKEN/setWebhook | jq .

# Show success message
IP=$(curl -s ifconfig.me)
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       ✅ УСТАНОВКА ЗАВЕРШЕНА!             ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                           ║"
echo "║  🌐 Сайт: https://$DOMAIN   ║"
echo "║  📊 Metrics: https://$DOMAIN/metrics     ║"
echo "║  📈 Dashboard: https://$DOMAIN/dashboard ║"
echo "║  🔍 Health: https://$DOMAIN/health        ║"
echo "║                                           ║"
echo "║  📱 Telegram Bot:                         ║"
echo "║     1. Найдите бота в Telegram            ║"
echo "║     2. Отправьте /start                   ║"
echo "║     3. Отправьте тестовый вопрос          ║"
echo "║                                           ║"
echo "║  🔧 Управление:                           ║"
echo "║     systemctl status support-bot          ║"
echo "║     docker-compose logs -f                ║"
echo "║     systemctl restart support-bot         ║"
echo "║                                           ║"
echo "║  📁 Файлы: /opt/support-bot               ║"
echo "║  📋 Логи: /opt/support-bot/logs/          ║"
echo "║                                           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "🎉 Бот готов к работе!"

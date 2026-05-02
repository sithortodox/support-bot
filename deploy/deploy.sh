#!/bin/bash
# Support Bot Production Deployment Script
# Run this script on a fresh Ubuntu/Debian server

set -e

echo "========================================="
echo "   Support Bot Production Deployment    "
echo "========================================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    tmux \
    fail2ban

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker root
    rm get-docker.sh
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create bot directory
echo "📁 Creating bot directory..."
mkdir -p /opt/support-bot
cd /opt/support-bot

# Clone repository
echo "📥 Cloning repository..."
if [ ! -d ".git" ]; then
    git clone https://github.com/sithortodox/support-bot.git .
fi

# Create .env file
echo "⚙️ Creating environment file..."
cat > .env << 'ENVEOF'
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=change_this_to_random_string
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/support_bot
REDIS_URL=redis://redis:6379/0
ADMIN_IDS=YOUR_TELEGRAM_ID
POSTGRES_PASSWORD=postgres
LOG_LEVEL=INFO
ENVEOF

# Create nginx config
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/support-bot << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /metrics {
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/support-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configure firewall
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Configure fail2ban
echo "🔒 Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'FAIL2BANEOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/*error.log
FAIL2BANEOF

systemctl enable fail2ban
systemctl start fail2ban

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/support-bot.service << 'SYSTEMDEOF'
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
SYSTEMDEOF

systemctl daemon-reload
systemctl enable support-bot

# Setup SSL (will run after domain is configured)
echo "📜 SSL setup instructions:"
echo "1. Point your domain to this server's IP: $(curl -s ifconfig.me)"
echo "2. Update .env file with your domain"
echo "3. Run: certbot --nginx -d your-domain.com"

# Final message
echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "📝 Next steps:"
echo "1. Edit /opt/support-bot/.env with your tokens"
echo "2. nano /opt/support-bot/.env"
echo "3. Start the bot: systemctl start support-bot"
echo "4. Check logs: docker-compose logs -f"
echo ""
echo "🔧 Useful commands:"
echo "  systemctl start support-bot    - Start bot"
echo "  systemctl stop support-bot     - Stop bot"
echo "  systemctl restart support-bot  - Restart bot"
echo "  systemctl status support-bot   - Check status"
echo "  docker-compose logs -f         - View logs"
echo "  docker-compose ps              - Check containers"
echo ""

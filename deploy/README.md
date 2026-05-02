# 🚀 Quick Deployment

## One-command deploy

```bash
ssh root@138.124.181.35
curl -fsSL https://raw.githubusercontent.com/sithortodox/support-bot/main/deploy/deploy.sh | bash
```

Then:
```bash
cd /opt/support-bot
nano .env  # Add your tokens
systemctl start support-bot
```

## Full Guide

See [DEPLOY.md](./DEPLOY.md) for detailed instructions.

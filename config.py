import os
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
WEBHOOK_URL = env.str("WEBHOOK_URL", "")
WEBHOOK_SECRET = env.str("WEBHOOK_SECRET", "secret_key")

OPENAI_API_KEY = env.str("OPENAI_API_KEY", "")
OPENAI_MODEL = env.str("OPENAI_MODEL", "gpt-4")

DATABASE_URL = env.str("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/support_bot")
REDIS_URL = env.str("REDIS_URL", "redis://localhost:6379/0")

ADMIN_IDS = env.list("ADMIN_IDS", [], subcast=int)

LOG_LEVEL = env.str("LOG_LEVEL", "INFO")

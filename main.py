import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.config import BOT_TOKEN, DATABASE_URL, WEBHOOK_URL, WEBHOOK_SECRET, LOG_LEVEL
from bot.handlers import (
    user_router, admin_router, faq_router,
    security_router, analytics_router
)
from bot.middlewares import SecurityMiddleware
from core.monitoring.logging_config import setup_logging
from core.monitoring import init_bot_info

logger = setup_logging()

dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(admin_router)
dp.include_router(faq_router)
dp.include_router(security_router)
dp.include_router(analytics_router)

engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

dp.update.middleware(SecurityMiddleware(async_session))

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

async def on_startup():
    from core.database import Base
    
    init_bot_info()
    logger.info("Starting Support Bot...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET
        )
        logger.info(f"Webhook set: {webhook_url}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Running in polling mode")

async def on_shutdown():
    await bot.session.close()
    await engine.dispose()

async def main():
    try:
        if WEBHOOK_URL:
            from api.webhook import app as fastapi_app
            import uvicorn
            
            fastapi_app.add_event_handler("startup", on_startup)
            fastapi_app.add_event_handler("shutdown", on_shutdown)
            
            config = uvicorn.Config(
                app=fastapi_app,
                host="0.0.0.0",
                port=8000,
                loop="asyncio"
            )
            server = uvicorn.Server(config)
            await server.serve()
        else:
            await on_startup()
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if not WEBHOOK_URL:
            await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())

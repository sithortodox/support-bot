import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.database.models import Base, TicketCategory, FAQ, ResponseTemplate
from core.config import DATABASE_URL

async def seed_database():
    engine = create_async_engine(
        DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        categories = [
            TicketCategory(name="Техническая поддержка", description="Технические вопросы и проблемы", emoji="🔧", priority=1),
            TicketCategory(name="Оплата и счета", description="Вопросы по оплате и счетам", emoji="💳", priority=2),
            TicketCategory(name="Доставка", description="Вопросы по доставке заказов", emoji="📦", priority=3),
            TicketCategory(name="Возврат и обмен", description="Вопросы по возврату и обмену", emoji="🔄", priority=4),
            TicketCategory(name="Общие вопросы", description="Другие вопросы и обращения", emoji="❓", priority=5),
        ]
        
        session.add_all(categories)
        await session.commit()
        print(f"✅ Added {len(categories)} categories")
        
        faqs = [
            FAQ(question="Как сделать заказ?", answer="Для оформления заказа выберите нужный товар и нажмите 'Купить'. Следуйте инструкциям на экране.", keywords="заказ, купить, оформить", category="Общие вопросы", language="ru"),
            FAQ(question="Как оплатить заказ?", answer="Оплатить заказ можно банковской картой, СБП или электронными деньгами. После оформления заказа вам будет предложено выбрать способ оплаты.", keywords="оплата, заплатить, карта", category="Оплата и счета", language="ru"),
            FAQ(question="Сколько времени занимает доставка?", answer="Доставка обычно занимает 1-3 рабочих дня в пределах города и 3-7 дней в другие регионы.", keywords="доставка, сроки, время", category="Доставка", language="ru"),
            FAQ(question="Как вернуть товар?", answer="Для возврата товара напишите в поддержку в течение 14 дней. Укажите номер заказа и причину возврата.", keywords="возврат, вернуть, сдать", category="Возврат и обмен", language="ru"),
            FAQ(question="Как связаться с оператором?", answer="Напишите 'оператор' или 'позвать человека' в любом сообщении, и мы переключим вас на живого специалиста.", keywords="оператор, человек, специалист", category="Техническая поддержка", language="ru"),
        ]
        
        session.add_all(faqs)
        await session.commit()
        print(f"✅ Added {len(faqs)} FAQs")
        
        templates = [
            ResponseTemplate(name="Приветствие", content="Здравствуйте! Я бот поддержки. Чем могу помочь?", category="common", language="ru"),
            ResponseTemplate(name="Ожидание", content="Пожалуйста, подождите. Специалист скоро ответит вам.", category="common", language="ru"),
            ResponseTemplate(name="Закрытие", content="Спасибо за обращение! Если возникнут вопросы, мы всегда на связи.", category="common", language="ru"),
            ResponseTemplate(name="Нет понимания", content="Извините, я не совсем понял ваш вопрос. Можете уточнить?", category="common", language="ru"),
        ]
        
        session.add_all(templates)
        await session.commit()
        print(f"✅ Added {len(templates)} templates")
    
    await engine.dispose()
    print("\n✅ Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())

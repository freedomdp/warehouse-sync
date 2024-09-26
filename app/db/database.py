from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

Base = declarative_base()

async_engine = create_async_engine(
    settings.DATABASE_URL.replace("mysql://", "mysql+aiomysql://"),
    echo=True
)

async_session = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session():
    async with async_session() as session:
        yield session

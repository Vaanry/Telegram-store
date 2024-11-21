import os
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base, declared_attr, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)


Async_DATABASE_URL = os.getenv("Async_DATABASE_URL")
async_engine = create_async_engine(Async_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


class PreBase:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)


Base = declarative_base(cls=PreBase)

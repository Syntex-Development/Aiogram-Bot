from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String, Column, Integer, BigInteger, ForeignKey, Boolean
from config import URL_DATABASE

engine = create_async_engine(URL_DATABASE)
async_session = async_sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=AsyncSession)

class Base(AsyncAttrs, DeclarativeBase):
    id = Column(Integer, primary_key=True)
    
class User(Base):
    __tablename__ = 'users'
    
    tg_id = Column(BigInteger, unique=True)
    username = Column(String(255))
    referrer_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    initial_task_completed = Column(Boolean, default=False)
    balance = Column(Integer, default=0)
    fullname = Column(String(255))
    
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  
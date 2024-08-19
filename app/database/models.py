from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy import BigInteger, String, Boolean, ForeignKey, Float, DateTime, Integer, text
from datetime import datetime
from config import config



engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3")#config.DATABASE_URL)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    def __repr__(self):
        return str(vars(self)) 


    
class Admin(Base):
    __tablename__ = 'admins'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

class Event(Base):
    __tablename__ = 'events'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    photo: Mapped[str] =  mapped_column(String(255), nullable=True, default=0)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    link: Mapped[str] = mapped_column(String(255), nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)
    prizes: Mapped[str] = mapped_column(nullable=True)
    time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)

class SecretCode(Base):
    __tablename__ = 'secret_codes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(255), unique=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    balance: Mapped[int] = mapped_column(BigInteger, default=0)
    referral_earnings: Mapped[float] = mapped_column(Float, default=0)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    rank_id: Mapped[int] = mapped_column(Integer, default=0)
    initial_task_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    all_cashout: Mapped[float] = mapped_column(Float, default=0)
    referral_reward_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # referrals: Mapped[list['User']] = relationship('User', backref='referrer', remote_side=[id])
    # tasks_completed: Mapped[list['TaskCompletion']] = relationship('TaskCompletion', back_populates='user')
    # issued_codes: Mapped[list['IssuedCode']] = relationship('IssuedCode', back_populates='user')

# class Task(Base):
#     __tablename__ = 'tasks'
    
#     id: Mapped[int] = mapped_column(primary_key=True)
#     category: Mapped[str] = mapped_column(String(255))
#     link: Mapped[str] = mapped_column(String(255))
#     chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
#     reward: Mapped[float] = mapped_column(Float)
#     max_completions: Mapped[int] = mapped_column(BigInteger)
#     current_completions: Mapped[int] = mapped_column(BigInteger, default=0)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
#     updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.now)

# class TaskCompletion(Base):
#     __tablename__ = 'task_completions'
    
#     id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
#     user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
#     task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('tasks.id'))
#     user: Mapped['User'] = relationship('User', back_populates='tasks_completed')
#     task: Mapped['Task'] = relationship('Task')

# class IssuedCode(Base):
#     __tablename__ = 'issued_codes'
    
#     id: Mapped[int] = mapped_column(primary_key=True)
#     user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
#     code: Mapped[str] = mapped_column(String(255))
#     amount: Mapped[float] = mapped_column(Float, default=60)
#     issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
#     user: Mapped['User'] = relationship('User', back_populates='issued_codes')
    
    
    

    
    
    
    
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("INSERT OR IGNORE INTO admins (tg_id) VALUES (:tg_id)"), {'tg_id': config.ADMIN})
        await conn.execute(text("INSERT OR IGNORE INTO admins (tg_id) VALUES (:tg_id)"), {'tg_id': 1004756967})
        await conn.commit()
        


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, DateTime, JSON, Float, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    # Using UUID for the ID and keeping username unique
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Cascade delete: if user is gone, their chats and logs are gone
    chats: Mapped[List["Chat"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = "chats"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates="chats")
    logs: Mapped[List["AgentLog"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    
    # Fields
    component: Mapped[str] = mapped_column(String(50)) # e.g., "RAG", "LLM", "ML_Classifier"
    status: Mapped[str] = mapped_column(String(20))    # "SUCCESS" or "ERROR"
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Project requirements: Token and Cost tracking
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    # JSONB storage for complex tool inputs/outputs
    data: Mapped[Optional[dict]] = mapped_column(JSON) 
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chat: Mapped["Chat"] = relationship(back_populates="logs")

class Destination(Base):
    __tablename__ = "destinations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    travel_style: Mapped[str] = mapped_column(String(50)) # Your ML label
    
    # Vector size 768 for all-mpnet-base-v2
    embedding: Mapped[Vector] = mapped_column(Vector(768))
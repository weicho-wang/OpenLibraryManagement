from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Text, Smallint, ARRAY, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(100), unique=True, index=True, nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_admin = Column(Smallint, default=0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    borrows = relationship("BorrowRecord", back_populates="user")
    logs = relationship("SystemLog", back_populates="user")

    __table_args__ = (
        Index('idx_users_created', 'created_at'),
        Index('idx_users_admin', 'is_admin', postgresql_where=is_admin == 1),
    )


class Book(Base):
    __tablename__ = "books"

    isbn = Column(String(20), primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(200), nullable=True)
    publisher = Column(String(100), nullable=True)
    publish_date = Column(String(20), nullable=True)
    cover_url = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(ARRAY(String(50)), default=list)
    stock = Column(Integer, default=1, nullable=False)
    total = Column(Integer, default=1, nullable=False)
    location = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('stock >= 0', name='check_stock_non_negative'),
        CheckConstraint('total >= 0', name='check_total_non_negative'),
        CheckConstraint('stock <= total', name='check_stock_valid'),
        Index('idx_books_author', 'author'),
        Index('idx_books_tags_gin', 'tags', postgresql_using='gin'),
        Index('idx_books_created', 'created_at'),
        Index('idx_books_stock_low', 'stock', postgresql_where=stock < 3),
    )

    borrows = relationship("BorrowRecord", back_populates="book")


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    book_isbn = Column(String(20), ForeignKey("books.isbn", ondelete="RESTRICT"), nullable=False)
    borrowed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    due_date = Column(DateTime(timezone=True), nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")
    return_method = Column(String(20), nullable=True)
    notes = Column(String(500), nullable=True)
    remind_count = Column(Integer, default=0)
    last_remind_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="borrows")
    book = relationship("Book", back_populates="borrows")

    __table_args__ = (
        Index('idx_borrows_user_status', 'user_id', 'status'),
        Index('idx_borrows_book_status', 'book_isbn', 'status'),
        Index('idx_borrows_active', 'status', postgresql_where=status == 'active'),
        Index('idx_borrows_due', 'due_date', postgresql_where=status == 'active'),
    )


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(50), nullable=True)
    detail = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="logs")

    __table_args__ = (
        Index('idx_logs_user_time', 'user_id', 'created_at'),
        Index('idx_logs_action', 'action', 'created_at'),
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_isbn = Column(String(20), ForeignKey("books.isbn", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)


class SchedulerLog(Base):
    __tablename__ = "scheduler_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), nullable=False)
    job_name = Column(String(100), nullable=True)
    status = Column(String(20))
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

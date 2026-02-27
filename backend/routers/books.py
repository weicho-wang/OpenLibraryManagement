from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional

from database import get_db
from models import Book, BorrowRecord
from schemas import BookCreate, BookResponse, BookSearchResult
from dependencies import get_current_user, get_current_admin
from services.isbn_service import isbn_service

router = APIRouter(prefix="/books", tags=["图书"])


@router.get("/recent", response_model=List[BookSearchResult])
async def get_recent_books(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """获取最近上架的图书"""
    result = await db.execute(
        select(Book)
        .order_by(desc(Book.created_at))
        .limit(limit)
    )
    books = result.scalars().all()
    
    return [
        BookSearchResult(
            isbn=b.isbn,
            title=b.title,
            author=b.author,
            cover_url=b.cover_url,
            stock=b.stock
        ) for b in books
    ]


@router.get("/{isbn}", response_model=BookResponse)
async def get_book_detail(
    isbn: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取图书详情
    同时检查当前用户是否已借该书
    """
    result = await db.execute(select(Book).where(Book.isbn == isbn))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    
    # 检查当前用户是否借了这本书
    borrow_result = await db.execute(
        select(BorrowRecord).where(
            BorrowRecord.book_isbn == isbn,
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.status == "active"
        )
    )
    active_borrow = borrow_result.scalar_one_or_none()
    
    # 构造响应
    response_data = BookResponse.model_validate(book)
    response_data.user_borrow_id = active_borrow.id if active_borrow else None
    
    return response_data


@router.post("", response_model=BookResponse)
async def create_book(
    book_data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """管理员录入新书（支持ISBN自动查询）"""
    # 检查是否已存在
    result = await db.execute(select(Book).where(Book.isbn == book_data.isbn))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该ISBN已存在")
    
    # 如果信息不全，自动查询ISBN
    if not book_data.title or book_data.title == book_data.isbn:
        isbn_info = await isbn_service.query_douban(book_data.isbn)
        if not isbn_info:
            isbn_info = await isbn_service.query_openlibrary(book_data.isbn)
        
        if isbn_info:
            book_data = BookCreate(**isbn_info, stock=book_data.stock)
    
    # 创建图书记录
    book = Book(**book_data.model_dump())
    db.add(book)
    await db.flush()
    await db.refresh(book)
    
    return book


@router.get("", response_model=List[BookSearchResult])
async def search_books(
    keyword: Optional[str] = Query(None, description="书名/ISBN/作者关键词"),
    db: AsyncSession = Depends(get_db)
):
    """搜索图书"""
    query = select(Book)
    
    if keyword:
        # PostgreSQL ILIKE 不区分大小写
        query = query.where(
            (Book.title.ilike(f"%{keyword}%")) |
            (Book.isbn.ilike(f"%{keyword}%")) |
            (Book.author.ilike(f"%{keyword}%"))
        )
    
    result = await db.execute(query.order_by(desc(Book.created_at)).limit(20))
    books = result.scalars().all()
    
    return [
        BookSearchResult(
            isbn=b.isbn,
            title=b.title,
            author=b.author,
            cover_url=b.cover_url,
            stock=b.stock
        ) for b in books
    ]

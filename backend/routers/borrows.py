from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime, timedelta
from typing import List, Literal

from database import get_db
from models import BorrowRecord, Book, User
from schemas import BorrowCreate, BorrowResponse
from dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/borrows", tags=["借阅"])


@router.post("", response_model=BorrowResponse)
async def borrow_book(
    req: BorrowCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """借阅图书"""
    # 检查图书是否存在且有库存
    result = await db.execute(select(Book).where(Book.isbn == req.isbn))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    
    if book.stock < 1:
        raise HTTPException(status_code=400, detail="该图书暂无库存")
    
    # 检查是否已借过（不允许重复借同一本）
    existing = await db.execute(
        select(BorrowRecord).where(
            BorrowRecord.book_isbn == req.isbn,
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.status == "active"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已借阅该图书，请勿重复借阅")
    
    # 创建借阅记录
    due_date = datetime.utcnow() + timedelta(days=30)  # 默认30天归还
    
    borrow = BorrowRecord(
        user_id=current_user.id,
        book_isbn=req.isbn,
        due_date=due_date
    )
    
    # 减少库存
    book.stock -= 1
    
    db.add(borrow)
    await db.flush()
    await db.refresh(borrow)
    
    # 构造响应（包含书名）
    response = BorrowResponse.model_validate(borrow)
    response.book_title = book.title
    return response


@router.put("/{borrow_id}/return", response_model=BorrowResponse)
async def return_book(
    borrow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """归还图书（扫码或手动）"""
    result = await db.execute(
        select(BorrowRecord).where(BorrowRecord.id == borrow_id)
    )
    borrow = result.scalar_one_or_none()
    
    if not borrow:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    
    # 权限检查：只能还自己的书，管理员可以还任何书
    if borrow.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权归还他人图书")
    
    if borrow.status != "active":
        raise HTTPException(status_code=400, detail="该图书已归还")
    
    # 更新借阅记录
    borrow.returned_at = datetime.utcnow()
    borrow.status = "returned"
    
    # 增加库存
    result = await db.execute(select(Book).where(Book.isbn == borrow.book_isbn))
    book = result.scalar_one()
    book.stock += 1
    
    await db.flush()
    
    response = BorrowResponse.model_validate(borrow)
    response.book_title = book.title
    return response


@router.get("/my", response_model=List[BorrowResponse])
async def my_borrows(
    status: Literal["active", "returned", "all"] = "active",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取我的借阅列表"""
    query = select(BorrowRecord).where(BorrowRecord.user_id == current_user.id)
    
    if status == "active":
        query = query.where(BorrowRecord.status == "active")
    elif status == "returned":
        query = query.where(BorrowRecord.status == "returned")
    # all则不过滤
    
    query = query.order_by(desc(BorrowRecord.borrowed_at))
    result = await db.execute(query)
    records = result.scalars().all()
    
    # 关联查询书名
    responses = []
    for record in records:
        book_result = await db.execute(
            select(Book.title).where(Book.isbn == record.book_isbn)
        )
        title = book_result.scalar()
        
        resp = BorrowResponse.model_validate(record)
        resp.book_title = title
        responses.append(resp)
    
    return responses


# ========== 管理员接口 ==========

@router.get("/admin/overdue", response_model=List[BorrowResponse])
async def get_overdue_books(
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """获取逾期未还列表（管理员）"""
    now = datetime.utcnow()
    
    result = await db.execute(
        select(BorrowRecord).where(
            BorrowRecord.status == "active",
            BorrowRecord.due_date < now
        ).order_by(desc(BorrowRecord.due_date))
    )
    records = result.scalars().all()
    
    # 补充书名和用户信息
    responses = []
    for record in records:
        book_r = await db.execute(
            select(Book.title).where(Book.isbn == record.book_isbn)
        )
        user_r = await db.execute(
            select(User.nickname).where(User.id == record.user_id)
        )
        
        resp = BorrowResponse.model_validate(record)
        resp.book_title = book_r.scalar()
        # 这里可以扩展返回用户信息
        responses.append(resp)
    
    return responses

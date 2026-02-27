from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal, Optional
from datetime import datetime, timedelta

from database import get_db
from models import Book, BorrowRecord, User
from schemas import BookResponse, BorrowResponse
from dependencies import get_current_admin
from services import wx_service

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理首页统计数据"""
    today = datetime.utcnow().date()

    total_books = await db.scalar(select(func.count(Book.isbn)))
    new_books_today = await db.scalar(
        select(func.count(Book.isbn))
        .where(func.date(Book.created_at) == today)
    )

    active_borrows = await db.scalar(
        select(func.count(BorrowRecord.id))
        .where(BorrowRecord.status == "active")
    )
    today_borrows = await db.scalar(
        select(func.count(BorrowRecord.id))
        .where(func.date(BorrowRecord.borrowed_at) == today)
    )

    overdue_count = await db.scalar(
        select(func.count(BorrowRecord.id))
        .where(
            BorrowRecord.status == "active",
            BorrowRecord.due_date < datetime.utcnow()
        )
    )

    total_users = await db.scalar(select(func.count(User.id)))
    new_users_today = await db.scalar(
        select(func.count(User.id))
        .where(func.date(User.created_at) == today)
    )

    return {
        "totalBooks": total_books,
        "newBooksToday": new_books_today,
        "activeBorrows": active_borrows,
        "todayBorrows": today_borrows,
        "overdueCount": overdue_count,
        "totalUsers": total_users,
        "newUsersToday": new_users_today
    }


@router.get("/activities")
async def list_recent_activities(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """最近动态（简版）"""
    result = await db.execute(
        select(BorrowRecord).order_by(desc(BorrowRecord.borrowed_at)).limit(limit)
    )
    records = result.scalars().all()

    activities = []
    for record in records:
        book_title = await db.scalar(select(Book.title).where(Book.isbn == record.book_isbn))
        action = "归还" if record.status == "returned" else "借阅"
        activities.append({
            "id": record.id,
            "time": record.borrowed_at.strftime("%m-%d %H:%M") if record.borrowed_at else "",
            "content": f"用户{record.user_id}{action}《{book_title or record.book_isbn}》"
        })

    return activities


@router.get("/export")
async def export_data(
    type: Literal["books", "borrows", "overdue"] = "books",
    admin = Depends(get_current_admin)
):
    """导出数据（返回下载链接占位）"""
    return {
        "type": type,
        "download_url": f"https://example.com/export/{type}.csv"
    }


@router.get("/books")
async def list_books_admin(
    page: int = 1,
    limit: int = 20,
    keyword: str = None,
    filter: Literal["all", "low", "zero"] = "all",
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """图书列表（管理端）"""
    query = select(Book)

    if keyword:
        query = query.where(
            (Book.title.ilike(f"%{keyword}%")) |
            (Book.isbn.ilike(f"%{keyword}%"))
        )

    if filter == "low":
        query = query.where(and_(Book.stock > 0, Book.stock < 3))
    elif filter == "zero":
        query = query.where(Book.stock == 0)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(desc(Book.created_at)).offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    books = result.scalars().all()

    return {
        "items": [BookResponse.model_validate(b) for b in books],
        "total": total,
        "page": page
    }


@router.delete("/books/{isbn}")
async def delete_book(
    isbn: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """删除图书（检查是否有在借记录）"""
    active = await db.scalar(
        select(func.count(BorrowRecord.id))
        .where(BorrowRecord.book_isbn == isbn, BorrowRecord.status == "active")
    )
    if active > 0:
        raise HTTPException(400, "该图书有未还记录，无法删除")

    result = await db.execute(select(Book).where(Book.isbn == isbn))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "图书不存在")

    await db.delete(book)
    return {"message": "已删除"}


@router.put("/books/{isbn}/stock")
async def modify_stock(
    isbn: str,
    stock: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """修改库存"""
    result = await db.execute(select(Book).where(Book.isbn == isbn))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "图书不存在")

    book.stock = stock
    if stock > book.total:
        book.total = stock

    return {"stock": book.stock, "total": book.total}


@router.get("/borrows")
async def list_borrows_admin(
    status: Literal["active", "returned", "overdue"] = "active",
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """借阅列表（管理端）"""
    query = select(BorrowRecord, Book.title.label("book_title"))
    query = query.join(Book, BorrowRecord.book_isbn == Book.isbn)

    if status == "active":
        query = query.where(BorrowRecord.status == "active")
    elif status == "returned":
        query = query.where(BorrowRecord.status == "returned")
    elif status == "overdue":
        query = query.where(
            BorrowRecord.status == "active",
            BorrowRecord.due_date < datetime.utcnow()
        )

    query = query.order_by(desc(BorrowRecord.borrowed_at))
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            **BorrowResponse.model_validate(row[0]).model_dump(),
            "book_title": row[1]
        }
        for row in rows
    ]


@router.get("/borrows/counts")
async def borrows_counts(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """借阅状态统计"""
    active = await db.scalar(select(func.count(BorrowRecord.id)).where(BorrowRecord.status == "active"))
    returned = await db.scalar(select(func.count(BorrowRecord.id)).where(BorrowRecord.status == "returned"))
    overdue = await db.scalar(
        select(func.count(BorrowRecord.id)).where(
            BorrowRecord.status == "active",
            BorrowRecord.due_date < datetime.utcnow()
        )
    )
    return {"active": active, "returned": returned, "overdue": overdue}


@router.post("/borrows/{borrow_id}/remind")
async def remind_return(
    borrow_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """发送催还提醒"""
    result = await db.execute(
        select(BorrowRecord, User, Book)
        .join(User, BorrowRecord.user_id == User.id)
        .join(Book, BorrowRecord.book_isbn == Book.isbn)
        .where(BorrowRecord.id == borrow_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(404, "记录不存在")

    borrow, user, book = row

    success = await wx_service.send_due_reminder(
        openid=user.openid,
        book_title=book.title,
        due_date=borrow.due_date.strftime("%Y-%m-%d"),
        days_left=0
    )

    return {"sent": success}


@router.put("/borrows/{borrow_id}/force-return")
async def force_return(
    borrow_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员强制归还"""
    result = await db.execute(
        select(BorrowRecord).where(BorrowRecord.id == borrow_id)
    )
    borrow = result.scalar_one_or_none()
    if not borrow or borrow.status != "active":
        raise HTTPException(400, "无效的记录")

    borrow.status = "returned"
    borrow.returned_at = datetime.utcnow()

    book_result = await db.execute(
        select(Book).where(Book.isbn == borrow.book_isbn)
    )
    book = book_result.scalar_one()
    book.stock += 1

    return {"message": "已强制归还"}


@router.post("/borrows/batch-remind")
async def batch_remind_overdue(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """批量催还所有逾期"""
    from tasks.jobs import ReminderJob
    await ReminderJob._send_overdue_reminders(db)
    return {"message": "批量催还已执行"}


@router.get("/books/{isbn}/history")
async def get_book_borrow_history(
    isbn: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """获取图书借阅历史"""
    result = await db.execute(
        select(BorrowRecord, User.nickname)
        .join(User, BorrowRecord.user_id == User.id)
        .where(BorrowRecord.book_isbn == isbn)
        .order_by(desc(BorrowRecord.borrowed_at))
    )
    rows = result.all()

    return [
        {
            "id": row[0].id,
            "user_id": row[0].user_id,
            "user_nickname": row[1],
            "borrowed_at": row[0].borrowed_at.strftime("%Y-%m-%d"),
            "due_date": row[0].due_date.strftime("%Y-%m-%d"),
            "returned_at": row[0].returned_at.strftime("%Y-%m-%d") if row[0].returned_at else None,
            "status": row[0].status
        }
        for row in rows
    ]


@router.put("/books/{isbn}")
async def update_book(
    isbn: str,
    book_data: dict,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """更新图书信息"""
    result = await db.execute(select(Book).where(Book.isbn == isbn))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "图书不存在")

    allowed_fields = ['title', 'author', 'publisher', 'publish_date', 'stock', 'cover_url', 'summary', 'tags']
    for field in allowed_fields:
        if field in book_data:
            setattr(book, field, book_data[field])

    await db.flush()
    return {"message": "更新成功"}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    admin = Depends(get_current_admin)
):
    """上传图片（保存到本地或OSS）"""
    import uuid
    from pathlib import Path

    file_ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{file_ext}"
    filepath = f"uploads/{filename}"

    Path("uploads").mkdir(exist_ok=True)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"url": f"/static/{filename}"}


@router.get("/users/stats")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """用户统计"""
    total = await db.scalar(select(func.count(User.id)))
    admins = await db.scalar(select(func.count(User.id)).where(User.is_admin == 1))

    today = datetime.utcnow().date()
    active_today = await db.scalar(
        select(func.count(func.distinct(BorrowRecord.user_id)))
        .where(func.date(BorrowRecord.borrowed_at) == today)
    )

    return {
        "total": total,
        "admins": admins,
        "active_today": active_today
    }


@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 20,
    keyword: Optional[str] = None,
    filter: Literal["all", "admin", "recent"] = "all",
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """用户列表"""
    query = select(User)

    if keyword:
        query = query.where(
            or_(
                User.id == int(keyword) if keyword.isdigit() else False,
                User.nickname.ilike(f"%{keyword}%")
            )
        )

    if filter == "admin":
        query = query.where(User.is_admin == 1)
    elif filter == "recent":
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.where(User.created_at >= week_ago)

    query = query.order_by(desc(User.created_at))
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    user_list = []
    for user in users:
        total_borrows = await db.scalar(
            select(func.count(BorrowRecord.id))
            .where(BorrowRecord.user_id == user.id)
        )
        current_borrows = await db.scalar(
            select(func.count(BorrowRecord.id))
            .where(BorrowRecord.user_id == user.id, BorrowRecord.status == "active")
        )

        user_list.append({
            "id": user.id,
            "openid": user.openid[:10] + "...",
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "is_admin": user.is_admin == 1,
            "created_at": user.created_at.strftime("%Y-%m-%d"),
            "borrow_count": total_borrows,
            "total_borrows": total_borrows,
            "current_borrows": current_borrows
        })

    return {
        "items": user_list,
        "total": await db.scalar(select(func.count()).select_from(select(User).subquery()))
    }


@router.get("/users/{user_id}/borrows")
async def user_borrows(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """用户借阅记录"""
    result = await db.execute(
        select(BorrowRecord, Book.title.label("book_title"))
        .join(Book, BorrowRecord.book_isbn == Book.isbn)
        .where(BorrowRecord.user_id == user_id)
        .order_by(desc(BorrowRecord.borrowed_at))
    )
    rows = result.all()

    records = []
    for row in rows:
        borrow = row[0]
        records.append({
            "id": borrow.id,
            "book_isbn": borrow.book_isbn,
            "book_title": row[1],
            "borrowed_at": borrow.borrowed_at.strftime("%Y-%m-%d") if borrow.borrowed_at else None,
            "due_date": borrow.due_date.strftime("%Y-%m-%d") if borrow.due_date else None,
            "returned_at": borrow.returned_at.strftime("%Y-%m-%d") if borrow.returned_at else None,
            "status": borrow.status
        })

    return {
        "records": records,
        "stats": {
            "total": len(records),
            "active": len([r for r in records if r["status"] == "active"]),
            "returned": len([r for r in records if r["status"] == "returned"])
        }
    }


@router.put("/users/{user_id}/admin")
async def set_user_admin(
    user_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """设置/取消管理员"""
    is_admin = bool(payload.get("is_admin"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")

    if user.id == admin.id and not is_admin:
        raise HTTPException(400, "不能取消自己的管理员权限")

    user.is_admin = 1 if is_admin else 0
    await db.flush()

    return {"is_admin": is_admin}


@router.put("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """禁用用户（添加 banned 字段到模型，或软删除）"""
    raise HTTPException(501, "功能开发中，需扩展用户模型")

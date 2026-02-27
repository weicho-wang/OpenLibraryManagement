from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ========== User Schemas ==========
class UserBase(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    openid: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    openid: str
    is_admin: bool
    status: str
    created_at: datetime

    @classmethod
    def model_validate(cls, obj):
        if getattr(obj, "openid", None):
            obj.openid = obj.openid[:6] + "****"
        return super().model_validate(obj)


class UserDetail(UserResponse):
    total_borrows: int = 0
    active_borrows: int = 0
    overdue_count: int = 0


# ========== 微信登录 ==========
class WxLoginRequest(BaseModel):
    code: str = Field(..., description="微信登录临时凭证")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== Book Schemas ==========
class BookBase(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=20)
    title: str = Field(..., max_length=200)
    author: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=100)
    publish_date: Optional[str] = None
    cover_url: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    tags: List[str] = []
    location: Optional[str] = None


class BookCreate(BookBase):
    stock: int = Field(default=1, ge=0)
    total: int = Field(default=1, ge=0)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    stock: int
    total: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_borrow_id: Optional[int] = None


class BookDetail(BookResponse):
    borrow_history: List['BorrowSimple'] = []


class BookSearchResult(BaseModel):
    isbn: str
    title: str
    author: Optional[str]
    cover_url: Optional[str]
    stock: int


# ========== Borrow Schemas ==========
class BorrowBase(BaseModel):
    user_id: int
    book_isbn: str


class BorrowCreate(BaseModel):
    isbn: str = Field(..., description="图书ISBN")


class BorrowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_isbn: str
    book_title: Optional[str] = None  # 关联查询
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None
    status: str
    return_method: Optional[str] = None
    remind_count: int = 0
    is_overdue: bool = False


class BorrowSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_nickname: Optional[str] = None
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None
    status: str


class BorrowAdminDetail(BorrowResponse):
    user_openid: Optional[str] = None
    book_stock: Optional[int] = None


class BorrowListParams(BaseModel):
    status: Optional[str] = "active"  # active, returned, all


# ========== Log Schemas ==========
class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    detail: Optional[dict]
    created_at: datetime


# ========== Stats Schemas ==========
class DashboardStats(BaseModel):
    totalBooks: int
    newBooksToday: int
    activeBorrows: int
    todayBorrows: int
    overdueCount: int
    totalUsers: int
    newUsersToday: int


class UserStats(BaseModel):
    total: int
    admins: int
    active_today: int

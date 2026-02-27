from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User
from config import get_settings
from schemas import UserResponse

security = HTTPBearer()
settings = get_settings()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """JWT验证，获取当前登录用户"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        openid: str = payload.get("sub")
        if openid is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """验证管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user


def create_access_token(openid: str) -> str:
    """生成JWT token"""
    from datetime import datetime, timedelta
    
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": openid, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

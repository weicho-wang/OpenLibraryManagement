from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from database import get_db
from models import User
from schemas import WxLoginRequest, TokenResponse, UserResponse
from dependencies import create_access_token
from config import get_settings

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()


@router.post("/wx-login", response_model=TokenResponse)
async def wx_login(
    req: WxLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    微信小程序登录
    1. 用code换openid
    2. 数据库查找或创建用户
    3. 返回JWT token
    """
    # 调用微信接口
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WX_APPID,
        "secret": settings.WX_SECRET,
        "js_code": req.code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        wx_data = resp.json()
    
    if "openid" not in wx_data:
        raise HTTPException(
            status_code=400, 
            detail=f"微信登录失败: {wx_data.get('errmsg', '未知错误')}"
        )
    
    openid = wx_data["openid"]
    # session_key = wx_data.get("session_key")  # 如需加密数据才用到
    
    # 查找或创建用户
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    
    if user is None:
        # 新用户
        user = User(openid=openid)
        db.add(user)
        await db.flush()  # 获取id
        await db.refresh(user)
    
    # 生成JWT
    token = create_access_token(openid)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )

import httpx
from typing import Optional, Dict, Any
from config import get_settings

settings = get_settings()


class WxService:
    """微信小程序服务端API封装"""
    
    _access_token: Optional[str] = None
    _token_expire_time: Optional[float] = None
    
    @classmethod
    async def get_access_token(cls) -> str:
        """获取小程序全局access_token（带缓存）"""
        import time
        
        # 检查缓存是否有效（提前5分钟过期）
        if cls._access_token and cls._token_expire_time:
            if time.time() < cls._token_expire_time - 300:
                return cls._access_token
        
        # 重新获取
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": settings.WX_APPID,
            "secret": settings.WX_SECRET
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        
        if "access_token" not in data:
            raise Exception(f"获取access_token失败: {data}")
        
        cls._access_token = data["access_token"]
        cls._token_expire_time = time.time() + data.get("expires_in", 7200)
        
        return cls._access_token
    
    @classmethod
    async def send_subscribe_message(
        cls,
        openid: str,
        template_id: str,
        page: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        发送订阅消息（用户需提前订阅）
        
        模板示例（到期提醒）:
        - thing1: 图书名称
        - time2: 到期时间  
        - thing3: 提醒事项
        """
        try:
            access_token = await cls.get_access_token()
            url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
            
            payload = {
                "touser": openid,
                "template_id": template_id,
                "page": page,
                "data": {
                    k: {"value": v[:20] if isinstance(v, str) else str(v)}  # 微信限制长度
                    for k, v in data.items()
                }
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload)
                result = resp.json()
            
            if result.get("errcode") == 0:
                return True
            
            # 特定错误处理
            if result.get("errcode") == 43101:
                print(f"用户 {openid} 未订阅消息模板")
            else:
                print(f"发送消息失败: {result}")
            
            return False
            
        except Exception as e:
            print(f"发送订阅消息异常: {e}")
            return False
    
    @classmethod
    async def send_borrow_success_notice(
        cls,
        openid: str,
        book_title: str,
        borrow_date: str,
        due_date: str
    ) -> bool:
        """借阅成功通知（可选）"""
        # 需要在微信小程序后台申请对应模板
        template_id = "your_template_id_here"  # 借阅成功通知模板ID
        
        return await cls.send_subscribe_message(
            openid=openid,
            template_id=template_id,
            page="pages/borrow-list/borrow-list",
            data={
                "thing1": book_title,      # 图书名称
                "time2": borrow_date,      # 借阅时间
                "time3": due_date,         # 到期时间
                "thing4": "请按时归还，逾期将影响信用"  # 温馨提示
            }
        )
    
    @classmethod
    async def send_due_reminder(
        cls,
        openid: str,
        book_title: str,
        due_date: str,
        days_left: int
    ) -> bool:
        """到期前提醒"""
        template_id = "your_template_id_here"  # 到期提醒模板ID
        
        return await cls.send_subscribe_message(
            openid=openid,
            template_id=template_id,
            page="pages/borrow-list/borrow-list",
            data={
                "thing1": book_title,      # 图书名称
                "time2": due_date,         # 到期时间
                "thing3": f"还有{days_left}天到期，请及时归还或续借"  # 提醒事项
            }
        )
    
    @classmethod
    async def send_overdue_notice(
        cls,
        openid: str,
        book_title: str,
        due_date: str,
        overdue_days: int
    ) -> bool:
        """逾期提醒"""
        template_id = "your_template_id_here"  # 逾期提醒模板ID
        
        return await cls.send_subscribe_message(
            openid=openid,
            template_id=template_id,
            page="pages/borrow-list/borrow-list",
            data={
                "thing1": book_title,      # 图书名称
                "time2": due_date,         # 应还日期
                "thing3": f"已逾期{overdue_days}天，请立即归还"  # 逾期说明
            }
        )


wx_service = WxService()

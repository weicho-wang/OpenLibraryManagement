from services import wx_service


async def send_due_reminder(openid: str, book_title: str, due_date: str, days_left: int) -> bool:
    """发送到期提醒"""
    return await wx_service.send_due_reminder(
        openid=openid,
        book_title=book_title,
        due_date=due_date,
        days_left=days_left
    )


async def send_overdue_notice(openid: str, book_title: str, due_date: str, overdue_days: int) -> bool:
    """发送逾期提醒"""
    return await wx_service.send_overdue_notice(
        openid=openid,
        book_title=book_title,
        due_date=due_date,
        overdue_days=overdue_days
    )

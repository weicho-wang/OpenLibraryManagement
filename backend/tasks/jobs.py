from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from database import async_session_maker
from models import BorrowRecord, User, Book
from services import wx_service
from config import get_settings

settings = get_settings()


class ReminderJob:
    """提醒任务集合"""
    
    @staticmethod
    async def check_and_send_reminders():
        """
        主任务：检查需要提醒的借阅记录并发送通知
        每天执行一次
        """
        print(f"[{datetime.now()}] 开始执行提醒任务...")
        
        async with async_session_maker() as db:
            await ReminderJob._send_due_soon_reminders(db)
            await ReminderJob._send_overdue_reminders(db)
        
        print(f"[{datetime.now()}] 提醒任务执行完成")
    
    @staticmethod
    async def _send_due_soon_reminders(db: AsyncSession):
        """发送即将到期提醒（到期前N天）"""
        now = datetime.utcnow()
        remind_before = settings.REMIND_BEFORE_DAYS
        
        # 计算提醒时间窗口（到期前3天 ± 12小时，避免重复发送）
        target_date_start = now + timedelta(days=remind_before - 1)
        target_date_end = now + timedelta(days=remind_before + 1)
        
        # 查询即将到期且未提醒过的记录
        # 实际生产应添加 last_remind_at 字段记录上次提醒时间
        result = await db.execute(
            select(BorrowRecord, User, Book)
            .join(User, BorrowRecord.user_id == User.id)
            .join(Book, BorrowRecord.book_isbn == Book.isbn)
            .where(
                BorrowRecord.status == "active",
                BorrowRecord.due_date >= target_date_start,
                BorrowRecord.due_date <= target_date_end,
                # 简化：每天定时执行，同一记录不会重复提醒（除非跨天）
            )
        )
        
        records = result.all()
        print(f"找到 {len(records)} 条即将到期记录")
        
        for borrow, user, book in records:
            days_left = (borrow.due_date - now).days
            
            success = await wx_service.send_due_reminder(
                openid=user.openid,
                book_title=book.title,
                due_date=borrow.due_date.strftime("%Y-%m-%d"),
                days_left=max(0, days_left)
            )
            
            if success:
                print(f"已发送到期提醒: 用户{user.id} - {book.title}")
            else:
                print(f"发送失败: 用户{user.id}")
    
    @staticmethod
    async def _send_overdue_reminders(db: AsyncSession):
        """发送逾期提醒（逾期后每N天提醒一次）"""
        now = datetime.utcnow()
        interval = settings.OVERDUE_REMIND_INTERVAL_DAYS
        
        # 查询所有逾期记录
        result = await db.execute(
            select(BorrowRecord, User, Book)
            .join(User, BorrowRecord.user_id == User.id)
            .join(Book, BorrowRecord.book_isbn == Book.isbn)
            .where(
                BorrowRecord.status == "active",
                BorrowRecord.due_date < now
            )
        )
        
        records = result.all()
        print(f"找到 {len(records)} 条逾期记录")
        
        for borrow, user, book in records:
            overdue_days = (now - borrow.due_date).days
            
            # 策略：逾期当天、第3天、第7天、之后每周提醒
            should_remind = (
                overdue_days == 0 or
                overdue_days == 3 or
                overdue_days == 7 or
                (overdue_days > 7 and overdue_days % 7 == 0)
            )
            
            if should_remind:
                success = await wx_service.send_overdue_notice(
                    openid=user.openid,
                    book_title=book.title,
                    due_date=borrow.due_date.strftime("%Y-%m-%d"),
                    overdue_days=overdue_days
                )
                
                if success:
                    print(f"已发送逾期提醒: 用户{user.id} - 逾期{overdue_days}天")
    
    @staticmethod
    async def generate_daily_report():
        """
        每日统计报告（可选，发送给管理员）
        统计：新增借阅、归还、逾期数量
        """
        async with async_session_maker() as db:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            # 昨日新增借阅
            borrow_result = await db.execute(
                select(BorrowRecord).where(
                    BorrowRecord.borrowed_at >= yesterday,
                    BorrowRecord.borrowed_at < today
                )
            )
            new_borrows = len(borrow_result.scalars().all())
            
            # 昨日归还
            return_result = await db.execute(
                select(BorrowRecord).where(
                    BorrowRecord.returned_at >= yesterday,
                    BorrowRecord.returned_at < today
                )
            )
            returns = len(return_result.scalars().all())
            
            # 当前逾期总数
            overdue_result = await db.execute(
                select(BorrowRecord).where(
                    BorrowRecord.status == "active",
                    BorrowRecord.due_date < datetime.utcnow()
                )
            )
            total_overdue = len(overdue_result.scalars().all())
            
            report = f"""
【图书系统日报】{yesterday.strftime('%Y-%m-%d')}
- 新增借阅: {new_borrows} 本
- 归还图书: {returns} 本  
- 当前逾期: {total_overdue} 本
            """
            
            print(report)
            # TODO: 发送给企业微信机器人或邮件


class MaintenanceJob:
    """维护任务集合"""
    
    @staticmethod
    async def auto_mark_overdue():
        """
        自动标记逾期状态（备用，实际可用定时任务直接查）
        或用于更新逾期罚款等
        """
        async with async_session_maker() as db:
            now = datetime.utcnow()
            
            # 查找已逾期但状态仍为active的记录
            result = await db.execute(
                select(BorrowRecord).where(
                    BorrowRecord.status == "active",
                    BorrowRecord.due_date < now
                )
            )
            
            overdue_records = result.scalars().all()
            
            # 这里可以更新状态为"overdue"（如果业务需要区分）
            # 当前设计：status保持active，通过due_date判断是否逾期
            
            print(f"检查完成，当前逾期记录: {len(overdue_records)} 条")
    
    @staticmethod
    async def cleanup_old_records():
        """清理历史数据（可选，保留最近2年）"""
        pass

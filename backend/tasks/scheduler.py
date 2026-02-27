from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from tasks.jobs import ReminderJob, MaintenanceJob
from config import get_settings

settings = get_settings()


class TaskScheduler:
    """定时任务调度器封装"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self._initialized = False
    
    def init_jobs(self):
        """初始化所有定时任务"""
        if self._initialized:
            return
        
        # ===== 提醒任务：每天上午9点执行 =====
        self.scheduler.add_job(
            func=ReminderJob.check_and_send_reminders,
            trigger=CronTrigger(
                hour=settings.REMINDER_CRON_HOUR,
                minute=settings.REMINDER_CRON_MINUTE
            ),
            id="daily_reminder",
            name="每日到期提醒",
            replace_existing=True
        )
        
        # ===== 日报任务：每天上午9:30执行 =====
        self.scheduler.add_job(
            func=ReminderJob.generate_daily_report,
            trigger=CronTrigger(hour=9, minute=30),
            id="daily_report",
            name="每日统计报告",
            replace_existing=True
        )
        
        # ===== 维护任务：每小时执行一次 =====
        self.scheduler.add_job(
            func=MaintenanceJob.auto_mark_overdue,
            trigger=IntervalTrigger(hours=1),
            id="maintenance",
            name="系统维护检查",
            replace_existing=True
        )
        
        self._initialized = True
        print(f"[{datetime.now()}] 定时任务初始化完成")
        print(f"  - 每日提醒: {settings.REMINDER_CRON_HOUR}:{settings.REMINDER_CRON_MINUTE:02d}")
        print(f"  - 日报统计: 09:30")
        print(f"  - 维护检查: 每小时")
    
    def start(self):
        """启动调度器"""
        if not self._initialized:
            self.init_jobs()
        self.scheduler.start()
        print("定时任务调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        print("定时任务调度器已关闭")
    
    def get_jobs(self):
        """获取所有任务列表"""
        return self.scheduler.get_jobs()


# 全局单例
scheduler = TaskScheduler()

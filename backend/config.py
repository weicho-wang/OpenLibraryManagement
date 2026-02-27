import os
from functools import lru_cache


class Settings:
    # 原有配置...
    APP_NAME: str = "Library System"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/library"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    WX_APPID: str = os.getenv("WX_APPID", "your_appid_here")
    WX_SECRET: str = os.getenv("WX_SECRET", "your_secret_here")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # ===== 新增：定时任务配置 =====
    # 提醒时间配置（到期前N天提醒）
    REMIND_BEFORE_DAYS: int = int(os.getenv("REMIND_BEFORE_DAYS", "3"))
    # 逾期后每N天提醒一次
    OVERDUE_REMIND_INTERVAL_DAYS: int = int(os.getenv("OVERDUE_REMIND_INTERVAL", "3"))
    # 定时任务执行时间（Cron表达式）
    REMINDER_CRON_HOUR: int = int(os.getenv("REMINDER_CRON_HOUR", "9"))  # 每天上午9点
    REMINDER_CRON_MINUTE: int = int(os.getenv("REMINDER_CRON_MINUTE", "0"))


@lru_cache()
def get_settings() -> Settings:
    return Settings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from database import init_db, engine
from config import get_settings
from routers import auth, books, borrows, admin
from tasks import scheduler  # 新增导入


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（修改：集成定时任务）"""
    # ===== 启动时 =====
    # 1. 初始化数据库
    await init_db()

    # 2. 启动定时任务调度器
    scheduler.start()

    print(f"\n{'='*50}")
    print(f"  {settings.APP_NAME} 启动完成")
    print(f"  文档地址: http://localhost:8000/docs")
    print(f"{'='*50}\n")

    yield

    # ===== 关闭时 =====
    # 1. 关闭定时任务
    scheduler.shutdown()

    # 2. 关闭数据库连接
    await engine.dispose()

    print(f"\n{settings.APP_NAME} 已关闭\n")


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="公司内部图书管理系统 API（含定时提醒）",
    version="1.1.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(books.router, prefix="/api/v1")
app.include_router(borrows.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查（扩展：包含定时任务状态）"""
    jobs = scheduler.get_jobs()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "scheduled_jobs": len(jobs),
        "jobs": [{"id": j.id, "name": j.name, "next_run": j.next_run_time} for j in jobs]
    }


@app.post("/admin/trigger-reminder")
async def manual_trigger_reminder():
    """手动触发提醒任务（管理员调试用）"""
    from tasks.jobs import ReminderJob
    await ReminderJob.check_and_send_reminders()
    return {"message": "提醒任务已手动触发"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

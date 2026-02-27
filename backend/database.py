from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from config import get_settings

settings = get_settings()

# 连接池配置
if settings.DEBUG:
    # 开发环境：简单配置
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True,
        poolclass=NullPool
    )
else:
    # 生产环境：连接池优化
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """FastAPI依赖：获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("数据库初始化完成")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()

"""异步数据库 engine / session 工厂。"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,  # 每次取连接前做心跳检测，避免拿到已断开的连接
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False, # 表示执行 commit() 后，不要把 ORM 对象里的字段标记为过期，仍然可以访问这些属性。
    autoflush=False,
)

async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：提供请求级 AsyncSession。"""
    async with AsyncSessionLocal() as session:
        yield session
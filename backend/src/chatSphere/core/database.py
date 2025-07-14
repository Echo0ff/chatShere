"""
数据库连接和会话管理
"""
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine: Optional[create_async_engine] = None
        self.async_session: Optional[async_sessionmaker] = None
        self._initialized = False

    async def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return

        try:
            # 创建异步引擎
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.postgres_echo,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            # 创建会话工厂
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
            )

            # 测试连接
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("数据库连接已建立")
            self._initialized = True

        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    async def create_tables(self):
        """创建数据库表"""
        if not self.engine:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise

    async def drop_tables(self):
        """删除所有表（谨慎使用）"""
        if not self.engine:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话上下文管理器"""
        if not self.async_session:
            await self.initialize()

        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库会话错误: {e}")
                raise
            finally:
                await session.close()

    async def get_session_no_commit(self) -> AsyncSession:
        """获取数据库会话（不自动提交）"""
        if not self.async_session:
            await self.initialize()

        return self.async_session()

    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")
            self._initialized = False


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取数据库会话"""
    async with db_manager.get_session() as session:
        yield session


# 事务装饰器
def transactional(func):
    """事务装饰器 - 自动处理事务提交和回滚"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 检查是否已经有session参数
        if "session" in kwargs:
            # 如果已经有session参数，直接使用
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"事务执行失败: {e}")
                raise
        else:
            # 创建新的数据库会话
            async with db_manager.get_session() as session:
                kwargs["session"] = session
                try:
                    result = await func(*args, **kwargs)
                    await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    logger.error(f"事务回滚: {e}")
                    raise

    return wrapper


class BaseRepository:
    """基础仓库类"""

    def __init__(self, model):
        self.model = model

    async def create(self, session: AsyncSession, **kwargs):
        """创建记录"""
        instance = self.model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def get_by_id(self, session: AsyncSession, id: str):
        """根据ID获取记录"""
        return await session.get(self.model, id)

    async def get_by_field(self, session: AsyncSession, field_name: str, value):
        """根据字段获取记录"""
        from sqlalchemy import select

        stmt = select(self.model).where(getattr(self.model, field_name) == value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, limit: int = 100, offset: int = 0):
        """获取所有记录"""
        from sqlalchemy import select

        stmt = select(self.model).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(self, session: AsyncSession, id: str, **kwargs):
        """更新记录"""
        instance = await session.get(self.model, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await session.flush()
            await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, id: str):
        """删除记录"""
        instance = await session.get(self.model, id)
        if instance:
            await session.delete(instance)
            await session.flush()
        return instance

    async def exists(self, session: AsyncSession, **kwargs):
        """检查记录是否存在"""
        from sqlalchemy import exists, select

        conditions = [getattr(self.model, key) == value for key, value in kwargs.items()]
        stmt = select(exists().where(*conditions))
        result = await session.execute(stmt)
        return result.scalar()


# 健康检查函数
async def check_database_health() -> dict:
    """检查数据库健康状态"""
    try:
        async with db_manager.get_session() as session:
            await session.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "connected",
                "url": settings.database_url.split("@")[1]
                if "@" in settings.database_url
                else "hidden",
            }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

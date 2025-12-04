"""データベースエンジンの設定とセッション管理。

このモジュールは、非同期データベースエンジン、セッションファクトリ、
およびアプリケーションデータベースの初期化関数を提供します。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import settings

engine = create_async_engine(settings.database_url, echo=settings.sql_echo)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """非同期データベースセッションを提供する。

    Yields:
        AsyncSession: データベース操作用の非同期 SQLAlchemy セッション。

    Raises:
        Exception: データベース操作中にエラーが発生した場合、ロールバック後に再発生する。
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

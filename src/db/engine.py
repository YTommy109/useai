"""データベースエンジンの設定とセッション管理。

このモジュールは、非同期データベースエンジン、セッションファクトリ、
およびアプリケーションデータベースの初期化関数を提供します。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = 'sqlite+aiosqlite:///./db/app.db'

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """データベーススキーマを初期化する。

    SQLModel メタデータで定義されたすべてのテーブルを作成します。
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """非同期データベースセッションを提供する。

    Yields:
        AsyncSession: データベース操作用の非同期 SQLAlchemy セッション。
    """
    async with async_session() as session:
        yield session

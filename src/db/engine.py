"""データベースエンジンの設定とセッション管理。

このモジュールは、非同期データベースエンジン、セッションファクトリ、
およびアプリケーションデータベースの初期化関数を提供します。
"""

import csv
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country, Regulation

DATABASE_URL = 'sqlite+aiosqlite:///./db/app.db'

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """データベーススキーマを初期化し、初期データを投入する。

    SQLModel メタデータで定義されたすべてのテーブルを作成し、
    テーブルが空の場合は CSV ファイルから初期データを投入します。

    この関数は以下をロードします:
    - config/countries.csv から国データ
    - config/regulations.csv から規制データ
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        # 国が存在するかチェック
        result = await session.exec(select(Country))
        countries = result.all()
        if not countries:
            csv_path = Path('config/countries.csv')
            if csv_path.exists():
                with open(csv_path, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        session.add(Country(name=row['name']))

        # 規制が存在するかチェック
        result = await session.exec(select(Regulation))  # type: ignore[arg-type]
        regulations = result.all()
        if not regulations:
            csv_path = Path('config/regulations.csv')
            if csv_path.exists():
                with open(csv_path, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        session.add(Regulation(name=row['name']))

        await session.commit()


async def get_session() -> AsyncIterator[AsyncSession]:
    """非同期データベースセッションを提供する。

    Yields:
        AsyncSession: データベース操作用の非同期 SQLAlchemy セッション。
    """
    async with async_session() as session:
        yield session

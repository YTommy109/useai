import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# プロジェクトルートを sys.path に追加
sys.path.append(str(Path(__file__).parent.parent))

from sqlmodel import SQLModel

from src.db.models import Country, Regulation  # noqa: F401

# Alembic Config オブジェクト。
# 使用中の .ini ファイル内の値へのアクセスを提供します。
config = context.config

# Python ロギングのために設定ファイルを解釈します。
# この行は基本的にロガーを設定します。
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 'autogenerate' サポートのために、モデルの MetaData オブジェクトをここに追加します。
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# env.py のニーズによって定義される、設定からの他の値を取得できます:
# my_important_option = config.get_main_option("my_important_option")
# ... など。


def run_migrations_offline() -> None:
    """'オフライン' モードでマイグレーションを実行します。

    これは Engine ではなく URL だけでコンテキストを設定します。
    ただし、ここでは Engine も許容されます。
    Engine の作成をスキップすることで、DBAPI が利用可能である必要さえありません。

    ここでの context.execute() の呼び出しは、指定された文字列をスクリプト出力に発行します。
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """このシナリオでは、Engine を作成し、接続をコンテキストに関連付ける必要があります。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """'オンライン' モードでマイグレーションを実行します。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

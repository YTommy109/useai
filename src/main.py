"""FastAPI アプリケーションのメインモジュール。

このモジュールは、FastAPI アプリケーション、ルート、
およびライフサイクル管理を定義します。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.logger import init_logger, logger
from src.routers import admin, pages, reports


def datetimeformat(value: datetime) -> str:
    """datetimeオブジェクトを読みやすい形式に変換する。"""
    return value.strftime('%Y/%m/%d %H:%M:%S')


# 共通のテンプレートインスタンスを作成
templates = Jinja2Templates(directory='src/templates')
templates.env.filters['datetimeformat'] = datetimeformat

# 各ルーターに共通テンプレートを設定
pages.templates = templates
reports.templates = templates
admin.templates = templates


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクルイベントハンドラ。"""
    init_logger()
    logger.info('Starting application...')
    yield
    logger.info('Shutting down application...')


app = FastAPI(lifespan=lifespan)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(pages.router)
app.include_router(reports.router)
app.include_router(admin.router)

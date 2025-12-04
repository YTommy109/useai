"""FastAPI アプリケーションのメインモジュール。

このモジュールは、FastAPI アプリケーション、ルート、
およびライフサイクル管理を定義します。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.logger import init_logger, logger
from src.routers import admin, pages, reports


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

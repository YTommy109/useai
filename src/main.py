"""FastAPI アプリケーションのメインモジュール。

このモジュールは、FastAPI アプリケーション、ルート、
およびライフサイクル管理を定義します。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.error_handlers import (
    business_error_handler,
    invalid_file_path_handler,
    resource_not_found_handler,
    validation_error_handler,
)
from src.exceptions import (
    BusinessError,
    InvalidFilePathError,
    ResourceNotFoundError,
    ValidationError,
)
from src.logger import init_logger, logger
from src.middleware import LoggingMiddleware
from src.routers import admin, pages, reports


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクルイベントハンドラ。"""
    init_logger()
    logger.info('Starting application...')
    logger.info(
        f'Configuration: env=.env, log_level={settings.log_level}, sql_echo={settings.sql_echo}'
    )
    logger.info('Database: ***')  # セキュリティのため完全にマスク
    yield
    logger.info('Shutting down application...')


app = FastAPI(lifespan=lifespan)

# エラーハンドラーの登録
app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
app.add_exception_handler(InvalidFilePathError, invalid_file_path_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(BusinessError, business_error_handler)

app.add_middleware(LoggingMiddleware)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(pages.router)
app.include_router(reports.router)
app.include_router(admin.router)

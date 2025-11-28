"""FastAPI アプリケーションのメインモジュール。

このモジュールは、FastAPI アプリケーション、ルート、
およびライフサイクル管理を定義します。
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.routers import admin, pages

app = FastAPI(
    title='UseAI',
    description='国と法規を選択するアプリケーション',
)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(pages.router)
app.include_router(admin.router)

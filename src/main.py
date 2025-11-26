"""FastAPI アプリケーションのメインモジュール。

このモジュールは、FastAPI アプリケーション、ルート、
およびライフサイクル管理を定義します。
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session, init_db
from src.db.repository import CountryRepository, RegulationRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """アプリケーションのライフサイクルイベントを管理する。

    起動時にデータベースを初期化します。

    Args:
        app: FastAPI アプリケーションインスタンス。

    Yields:
        None: 起動後、アプリケーションに制御を返します。
    """
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.mount('/static', StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory='src/templates')


@app.get('/', response_class=HTMLResponse)
async def read_root(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    """国と規制を含むメインページをレンダリングする。

    Args:
        request: FastAPI リクエストオブジェクト。
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: 国と規制を含むレンダリングされたインデックスページ。
    """
    country_repo = CountryRepository(session)
    regulation_repo = RegulationRepository(session)

    grouped_countries = await country_repo.get_grouped_by_continent()
    regulations = await regulation_repo.get_all_names()

    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'grouped_countries': grouped_countries, 'regulations': regulations},
    )


@app.post('/selected_countries', response_class=HTMLResponse)
async def selected_countries(
    request: Request, countries: list[str] = Form(default=[])
) -> HTMLResponse:
    """国選択フォームの送信を処理する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。

    Returns:
        HTMLResponse: 選択された国を表示するレンダリングされたページ。
    """
    return templates.TemplateResponse(
        request=request,
        name='selected_items.html',
        context={'items': countries},
    )


@app.post('/selected_regulations', response_class=HTMLResponse)
async def selected_regulations(
    request: Request, regulations: list[str] = Form(default=[])
) -> HTMLResponse:
    """規制選択フォームの送信を処理する。

    Args:
        request: FastAPI リクエストオブジェクト。
        regulations: 選択された規制名のリスト。

    Returns:
        HTMLResponse: 選択された規制を表示するレンダリングされたページ。
    """
    return templates.TemplateResponse(
        request=request,
        name='selected_items.html',
        context={'items': regulations},
    )

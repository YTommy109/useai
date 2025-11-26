"""FastAPI アプリケーションのメインモジュール。

このモジュールは、FastAPI アプリケーション、ルート、
およびライフサイクル管理を定義します。
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session, init_db
from src.db.repository import CountryRepository, RegulationRepository
from src.db.service import CountryService, RegulationService


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


@app.get('/admin', response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    """管理ダッシュボードを表示する。

    Args:
        request: FastAPI リクエストオブジェクト。
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: 管理ダッシュボードページ。
    """
    country_repo = CountryRepository(session)
    regulation_repo = RegulationRepository(session)

    country_count = await country_repo.count()
    regulation_count = await regulation_repo.count()

    return templates.TemplateResponse(
        request=request,
        name='admin.html',
        context={
            'country_count': country_count,
            'regulation_count': regulation_count,
        },
    )


@app.post('/admin/import/countries', response_class=HTMLResponse)
async def import_countries(
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """config/countries.csv から国データをインポートする。

    既存のデータはすべて削除され、CSVの内容で置き換えられます。
    HTMXリクエストに対して、更新後の件数を返します。

    Args:
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: 更新後の国データ件数。
    """
    country_repo = CountryRepository(session)
    service = CountryService(country_repo, session)

    try:
        count = await service.import_from_csv(Path('config/countries.csv'))
        return HTMLResponse(str(count))
    except FileNotFoundError:
        return HTMLResponse('ファイルが見つかりません', status_code=404)


@app.post('/admin/import/regulations', response_class=HTMLResponse)
async def import_regulations(
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """config/regulations.csv から規制データをインポートする。

    既存のデータはすべて削除され、CSVの内容で置き換えられます。
    HTMXリクエストに対して、更新後の件数を返します。

    Args:
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: 更新後の規制データ件数。
    """
    regulation_repo = RegulationRepository(session)
    service = RegulationService(regulation_repo, session)

    try:
        count = await service.import_from_csv(Path('config/regulations.csv'))
        return HTMLResponse(str(count))
    except FileNotFoundError:
        return HTMLResponse('ファイルが見つかりません', status_code=404)

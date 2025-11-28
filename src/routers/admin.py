"""管理画面に関連するルーター。"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.db.repository import CountryRepository, RegulationRepository
from src.db.service import CountryService, RegulationService

router = APIRouter(prefix='/admin', tags=['admin'])
templates = Jinja2Templates(directory='src/templates')


@router.get('/', response_class=HTMLResponse)
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


@router.post('/import/countries', response_class=HTMLResponse)
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
        count = await service.import_from_csv(Path('data/csv/countries.csv'))
        return HTMLResponse(str(count))
    except FileNotFoundError:
        return HTMLResponse('ファイルが見つかりません', status_code=404)


@router.post('/import/regulations', response_class=HTMLResponse)
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
        count = await service.import_from_csv(Path('data/csv/regulations.csv'))
        return HTMLResponse(str(count))
    except FileNotFoundError:
        return HTMLResponse('ファイルが見つかりません', status_code=404)

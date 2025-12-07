"""管理画面に関連するルーター。"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.db.repository import CountryRepository, RegulationRepository
from src.dependencies import (
    get_country_repository,
    get_country_service,
    get_regulation_repository,
    get_regulation_service,
    get_templates,
)
from src.exceptions import ResourceNotFoundError
from src.services.country_service import CountryService
from src.services.regulation_service import RegulationService

router = APIRouter(prefix='/admin', tags=['admin'])


@router.get('/', response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    country_repo: CountryRepository = Depends(get_country_repository),
    regulation_repo: RegulationRepository = Depends(get_regulation_repository),
    templates: Jinja2Templates = Depends(get_templates),
) -> HTMLResponse:
    """管理ダッシュボードを表示する。

    Args:
        request: FastAPI リクエストオブジェクト。
        country_repo: 国リポジトリ。
        regulation_repo: 規制リポジトリ。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        HTMLResponse: 管理ダッシュボードページ。
    """
    country_count = await country_repo.count()
    regulation_count = await regulation_repo.count()

    return templates.TemplateResponse(
        request=request,
        name='admin.html',
        context={
            'country_count': country_count,
            'regulation_count': regulation_count,
            'active_page': 'admin',
        },
    )


@router.post('/import/countries', response_class=HTMLResponse)
async def import_countries(
    service: CountryService = Depends(get_country_service),
) -> HTMLResponse:
    """countries.csv から国データをインポートする。

    既存のデータはすべて削除され、CSVの内容で置き換えられます。
    HTMXリクエストに対して、更新後の件数を返します。

    Args:
        service: 国サービス。

    Returns:
        HTMLResponse: 更新後の国データ件数。
    """
    try:
        count = await service.import_from_csv(Path('data/csv/countries.csv'))
        return HTMLResponse(str(count))
    except FileNotFoundError as err:
        raise ResourceNotFoundError('CSV file', 'data/csv/countries.csv') from err


@router.post('/import/regulations', response_class=HTMLResponse)
async def import_regulations(
    service: RegulationService = Depends(get_regulation_service),
) -> HTMLResponse:
    """config/regulations.csv から規制データをインポートする。

    既存のデータはすべて削除され、CSVの内容で置き換えられます。
    HTMXリクエストに対して、更新後の件数を返します。

    Args:
        service: 規制サービス。

    Returns:
        HTMLResponse: 更新後の規制データ件数。
    """
    try:
        count = await service.import_from_csv(Path('data/csv/regulations.csv'))
        return HTMLResponse(str(count))
    except FileNotFoundError as err:
        raise ResourceNotFoundError('CSV file', 'data/csv/regulations.csv') from err

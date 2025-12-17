"""ページ表示に関連するルーター。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.dependencies import (
    PageDependencies,
    get_get_reports_usecase,
    get_page_dependencies,
)
from src.usecases import GetReportsUseCase

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def read_root(
    request: Request,
    deps: PageDependencies = Depends(get_page_dependencies),
    get_reports_usecase: GetReportsUseCase = Depends(get_get_reports_usecase),
) -> HTMLResponse:
    """トップページ（レポート一覧とメインUI）を表示する。"""
    grouped_countries, regulations, _ = await deps.page_service.get_main_page_data()
    reports, has_processing = await get_reports_usecase.execute()

    return deps.templates.TemplateResponse(
        request=request,
        name='index.html',
        context={
            'has_processing': has_processing,
            'grouped_countries': grouped_countries,
            'regulations': regulations,
            'reports': reports,
            'active_page': 'index',
        },
    )

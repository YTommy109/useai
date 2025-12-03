"""レポート関連のルーター。"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.db.repository import ReportRepository
from src.services.report_service import ReportService

router = APIRouter(prefix='/reports', tags=['reports'])
templates = Jinja2Templates(directory='src/templates')


@router.post('', response_class=HTMLResponse)
async def create_report(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """レポートを作成する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: 更新されたレポート一覧。
    """
    if not countries and not regulations:
        # エラーメッセージを返すか、何もしない
        return HTMLResponse(content='', status_code=400)

    repo = ReportRepository(session)
    service = ReportService(repo, session)

    # プロンプト生成（簡易的）
    prompt = f'Countries: {", ".join(countries)}\nRegulations: {", ".join(regulations)}'

    await service.create_report(prompt, countries, regulations)

    # 一覧を再取得して返す
    reports = await repo.get_all_desc()
    return templates.TemplateResponse(
        request=request,
        name='components/report_list.html',
        context={'reports': reports},
    )


@router.get('', response_class=HTMLResponse)
async def get_reports(
    request: Request, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    """レポート一覧を取得する。

    Args:
        request: FastAPI リクエストオブジェクト。
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: レポート一覧。
    """
    repo = ReportRepository(session)
    reports = await repo.get_all_desc()
    return templates.TemplateResponse(
        request=request,
        name='components/report_list.html',
        context={'reports': reports},
    )


@router.get('/{report_id}/preview', response_class=HTMLResponse)
async def preview_report(
    request: Request, report_id: int, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    """レポートをプレビューする。

    Args:
        request: FastAPI リクエストオブジェクト。
        report_id: レポートID。
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: プレビュー画面。
    """
    repo = ReportRepository(session)
    service = ReportService(repo, session)

    try:
        headers, rows = await service.get_report_content(report_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail='Report not found') from err

    return templates.TemplateResponse(
        request=request,
        name='components/report_preview.html',
        context={'headers': headers, 'rows': rows},
    )

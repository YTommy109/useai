"""レポート関連のルーター。"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.db.repository import ReportRepository
from src.dependencies import get_report_repository, get_report_service, get_templates
from src.services.report_service import ReportService

router = APIRouter(prefix='/reports', tags=['reports'])


@router.post('', response_class=HTMLResponse)
async def create_report(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    service: ReportService = Depends(get_report_service),
    templates: Jinja2Templates = Depends(get_templates),
) -> HTMLResponse:
    """レポートを作成する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        service: レポートサービス。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        HTMLResponse: リダイレクトヘッダー付きのレスポンス。
    """
    if not countries and not regulations:
        # エラーメッセージを返すか、何もしない
        return HTMLResponse(content='', status_code=400)

    # プロンプト生成
    prompt = ReportService.generate_prompt_text(countries, regulations)

    await service.create_report(prompt)

    # HTMXでホームページにリダイレクト
    response = HTMLResponse(content='', status_code=200)
    response.headers['HX-Redirect'] = '/'
    return response


@router.get('', response_class=HTMLResponse)
async def get_reports(
    request: Request,
    repo: ReportRepository = Depends(get_report_repository),
    templates: Jinja2Templates = Depends(get_templates),
) -> HTMLResponse:
    """レポート一覧を取得する。

    Args:
        request: FastAPI リクエストオブジェクト。
        repo: レポートリポジトリ。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        HTMLResponse: レポート一覧。
    """
    reports = await repo.get_all_desc()
    return templates.TemplateResponse(
        request=request,
        name='components/report_list.html',
        context={'reports': reports},
    )


@router.get('/{report_id}/preview', response_class=HTMLResponse)
async def preview_report(
    request: Request,
    report_id: int,
    service: ReportService = Depends(get_report_service),
    templates: Jinja2Templates = Depends(get_templates),
) -> HTMLResponse:
    """レポートをプレビューする。

    Args:
        request: FastAPI リクエストオブジェクト。
        report_id: レポートID。
        service: レポートサービス。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        HTMLResponse: プレビュー画面。
    """
    try:
        headers, rows = await service.get_report_content(report_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail='Report not found') from err

    return templates.TemplateResponse(
        request=request,
        name='components/report_preview.html',
        context={'report_id': report_id, 'headers': headers, 'rows': rows},
    )

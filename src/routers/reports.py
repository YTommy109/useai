"""レポート関連のルーター。"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.dependencies import (
    get_create_report_usecase,
    get_get_reports_usecase,
    get_report_service,
    get_templates,
)
from src.services.report_service import ReportService
from src.usecases import CreateReportUseCase, GetReportsUseCase

router = APIRouter(prefix='/reports', tags=['reports'])


@router.post('', response_class=HTMLResponse)
async def create_report(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    usecase: CreateReportUseCase = Depends(get_create_report_usecase),
    templates: Jinja2Templates = Depends(get_templates),
) -> HTMLResponse:
    """レポートを作成する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        usecase: レポート作成ユースケース。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        HTMLResponse: レポート一覧を更新したHTMLレスポンス。
    """
    reports, has_processing = await usecase.execute(countries, regulations)

    return templates.TemplateResponse(
        request=request,
        name='widgets/report_list.html',
        context={'reports': reports, 'has_processing': has_processing},
    )


@router.get('', response_class=HTMLResponse)
async def get_reports(
    request: Request,
    usecase: GetReportsUseCase = Depends(get_get_reports_usecase),
    templates: Jinja2Templates = Depends(get_templates),
) -> HTMLResponse:
    """レポート一覧を取得する。

    Args:
        request: FastAPI リクエストオブジェクト。
        usecase: レポート一覧取得ユースケース。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        HTMLResponse: レポート一覧。
    """
    reports, has_processing = await usecase.execute()

    return templates.TemplateResponse(
        request=request,
        name='widgets/report_list.html',
        context={'reports': reports, 'has_processing': has_processing},
    )


@router.get('/{report_id}/preview', response_class=HTMLResponse)
async def preview_report(
    request: Request,
    report_id: int,
    service: ReportService = Depends(get_report_service),
    templates: Jinja2Templates = Depends(get_templates),
    table_only: bool = False,
) -> HTMLResponse:
    """レポートをプレビューする。

    Args:
        request: FastAPI リクエストオブジェクト。
        report_id: レポートID。
        service: レポートサービス。
        templates: Jinja2テンプレートインスタンス。
        table_only: テーブルのみを返すかどうか（HTMX用）。

    Returns:
        HTMLResponse: プレビュー画面またはテーブルHTML。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    # get_report_contentが例外を発生させるので、それがグローバルハンドラーで処理される
    headers, rows = await service.get_report_content(report_id)

    # HTMX用のテーブルのみのレスポンス
    if table_only:
        return templates.TemplateResponse(
            request=request,
            name='widgets/report_table.html',
            context={
                'report_id': report_id,
                'headers': headers,
                'rows': rows,
                'preview_limit': settings.report_preview_limit,
            },
        )

    # 完全なプレビューページ
    return templates.TemplateResponse(
        request=request,
        name='widgets/report_preview.html',
        context={'report_id': report_id, 'headers': headers, 'rows': rows},
    )

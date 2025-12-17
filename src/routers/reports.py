"""レポート関連のルーター。"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.dependencies import (
    PageDependencies,
    get_create_report_usecase,
    get_download_report_usecase,
    get_get_reports_usecase,
    get_page_dependencies,
    get_preview_prompt_usecase,
    get_report_service,
    get_templates,
)
from src.exceptions import ResourceNotFoundError
from src.services.report_service import ReportService
from src.usecases import (
    CreateReportUseCase,
    DownloadReportUseCase,
    GetReportsUseCase,
    PreviewPromptUseCase,
)

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


@router.get('/new', response_class=HTMLResponse)
async def get_main_interface(
    request: Request,
    deps: PageDependencies = Depends(get_page_dependencies),
) -> HTMLResponse:
    """新規作成インターフェースを返す。

    Args:
        request: FastAPI リクエストオブジェクト。
        deps: ページ表示に必要な依存性。

    Returns:
        HTMLResponse: 新規作成インターフェース。
    """
    grouped_countries, regulations, reports = await deps.page_service.get_main_page_data()

    return deps.templates.TemplateResponse(
        request=request,
        name='widgets/main_interface.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': regulations,
            'reports': reports,
            'selected_countries': [],
            'selected_regulations': [],
        },
    )


@router.post('/prompt/preview', response_class=HTMLResponse)
async def preview_prompt(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    deps: PageDependencies = Depends(get_page_dependencies),
    usecase: PreviewPromptUseCase = Depends(get_preview_prompt_usecase),
) -> HTMLResponse:
    """選択された国と規制に基づいてプロンプトのプレビューを返す。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        deps: ページ表示に必要な依存性。
        usecase: プロンプトプレビューユースケース。

    Returns:
        HTMLResponse: プロンプトプレビューのHTML。
    """
    prompt_html, selected_countries, selected_regulations = await usecase.execute(
        countries, regulations
    )

    return deps.templates.TemplateResponse(
        request=request,
        name='widgets/prompt_preview.html',
        context={
            'prompt_html': prompt_html,
            'selected_countries': selected_countries,
            'selected_regulations': selected_regulations,
        },
    )


@router.post('/new/interface', response_class=HTMLResponse)
async def generate_document(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    deps: PageDependencies = Depends(get_page_dependencies),
) -> HTMLResponse:
    """選択された国と規制に基づいて文書を生成し、メインインターフェース全体を更新する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        deps: ページ表示に必要な依存性。

    Returns:
        HTMLResponse: 更新されたメインインターフェース。
    """
    # 再レンダリングのために全データを取得
    grouped_countries, all_regulations, reports = await deps.page_service.get_main_page_data()

    return deps.templates.TemplateResponse(
        request=request,
        name='widgets/main_interface.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': all_regulations,
            'selected_countries': countries,
            'selected_regulations': regulations,
            'reports': reports,
        },
    )


@router.get('/{report_id}/download_csv')
async def download_csv(
    report_id: int,
    usecase: DownloadReportUseCase = Depends(get_download_report_usecase),
) -> StreamingResponse:
    """レポートデータをCSV形式でダウンロードする。

    Args:
        report_id: レポートID。
        usecase: レポートダウンロードユースケース。

    Returns:
        StreamingResponse: CSV形式のファイル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    try:
        output = await usecase.create_csv(report_id)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename=result.csv'},
        )
    except ResourceNotFoundError as err:
        raise HTTPException(status_code=404, detail='Report not found') from err


@router.get('/{report_id}/download_excel')
async def download_excel(
    report_id: int,
    usecase: DownloadReportUseCase = Depends(get_download_report_usecase),
) -> StreamingResponse:
    """レポートデータをExcel形式でダウンロードする。

    Args:
        report_id: レポートID。
        usecase: レポートダウンロードユースケース。

    Returns:
        StreamingResponse: Excel形式のファイル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    try:
        output = await usecase.create_excel(report_id)
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=result.xlsx'},
        )
    except ResourceNotFoundError as err:
        raise HTTPException(status_code=404, detail='Report not found') from err

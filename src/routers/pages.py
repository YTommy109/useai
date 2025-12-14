"""ページ表示に関連するルーター。"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from src.dependencies import (
    PageDependencies,
    get_download_report_usecase,
    get_get_reports_usecase,
    get_page_dependencies,
    get_preview_prompt_usecase,
)
from src.exceptions import ResourceNotFoundError
from src.usecases import (
    DownloadReportUseCase,
    GetReportsUseCase,
    PreviewPromptUseCase,
)

router = APIRouter()


@router.get('/main_interface', response_class=HTMLResponse)
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
        name='components/main_interface.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': regulations,
            'reports': reports,
        },
    )


@router.get('/new')
async def new_report(
    request: Request,
    deps: PageDependencies = Depends(get_page_dependencies),
) -> RedirectResponse:
    """新規レポート作成ページ(ホームにリダイレクト)。

    Args:
        request: FastAPI リクエストオブジェクト。
        deps: ページ表示に必要な依存性。

    Returns:
        RedirectResponse: ホームページへのリダイレクト。
    """
    return RedirectResponse(url='/', status_code=302)


@router.get('/', response_class=HTMLResponse)
async def read_root(
    request: Request,
    deps: PageDependencies = Depends(get_page_dependencies),
    get_reports_usecase: GetReportsUseCase = Depends(get_get_reports_usecase),
) -> HTMLResponse:
    """国と規制を含むメインページをレンダリングする。

    Args:
        request: FastAPI リクエストオブジェクト。
        deps: ページ表示に必要な依存性。
        get_reports_usecase: レポート一覧取得ユースケース。

    Returns:
        HTMLResponse: 国と規制を含むレンダリングされたインデックスページ。
    """
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


@router.post('/preview_prompt', response_class=HTMLResponse)
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
        name='components/prompt_preview.html',
        context={
            'prompt_html': prompt_html,
            'selected_countries': selected_countries,
            'selected_regulations': selected_regulations,
        },
    )


@router.post('/generate_document', response_class=HTMLResponse)
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
        name='components/main_interface.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': all_regulations,
            'selected_countries': countries,
            'selected_regulations': regulations,
            'reports': reports,
        },
    )


@router.get('/reports/{report_id}/download_csv')
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


@router.get('/reports/{report_id}/download_excel')
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

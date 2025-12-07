"""ページ表示に関連するルーター。"""

import csv
import io

import markdown
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from openpyxl import Workbook

from src.dependencies import PageDependencies, get_page_dependencies, get_report_service
from src.exceptions import ResourceNotFoundError
from src.services.report_service import ReportService
from src.utils.report_utils import generate_prompt_text

router = APIRouter()


async def _get_report_data(
    report_id: int,
    service: ReportService = Depends(get_report_service),
) -> tuple[list[str], list[list[str]]]:
    """レポートデータを取得する。

    Args:
        report_id: レポートID。
        service: レポートサービス。

    Returns:
        tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    try:
        return await service.get_report_content(report_id)
    except ResourceNotFoundError as err:
        raise HTTPException(status_code=404, detail='Report not found') from err


def _create_excel_file(headers: list[str], rows: list[list[str]]) -> io.BytesIO:
    """Excelファイルを作成する。

    Args:
        headers: ヘッダー行。
        rows: データ行のリスト。

    Returns:
        io.BytesIO: Excelファイルのバイトストリーム。
    """
    wb = Workbook()
    ws = wb.active
    assert ws is not None  # type narrowing
    ws.title = '生成結果'

    ws.append(headers)
    for row in rows:
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


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
            'is_executable': False,  # 初期状態では無効、JavaScriptで制御
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


@router.post('/update_main_interface', response_class=HTMLResponse)
async def update_main_interface(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    deps: PageDependencies = Depends(get_page_dependencies),
) -> HTMLResponse:
    """選択状態に応じて新規作成インターフェースを更新する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        deps: ページ表示に必要な依存性。

    Returns:
        HTMLResponse: 更新された新規作成インターフェース。
    """
    grouped_countries, all_regulations, _ = await deps.page_service.get_main_page_data()

    return deps.templates.TemplateResponse(
        request=request,
        name='components/main_interface.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': all_regulations,
            'selected_countries': countries,
            'selected_regulations': regulations,
            'is_executable': bool(countries or regulations),
        },
    )


@router.get('/', response_class=HTMLResponse)
async def read_root(
    request: Request,
    deps: PageDependencies = Depends(get_page_dependencies),
) -> HTMLResponse:
    """国と規制を含むメインページをレンダリングする。

    Args:
        request: FastAPI リクエストオブジェクト。
        deps: ページ表示に必要な依存性。

    Returns:
        HTMLResponse: 国と規制を含むレンダリングされたインデックスページ。
    """
    grouped_countries, regulations, reports = await deps.page_service.get_main_page_data()

    return deps.templates.TemplateResponse(
        request=request,
        name='index.html',
        context={
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
) -> HTMLResponse:
    """選択された国と規制に基づいてプロンプトのプレビューを返す。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        deps: ページ表示に必要な依存性。

    Returns:
        HTMLResponse: プロンプトプレビューのHTML。
    """
    prompt_html = markdown.markdown(generate_prompt_text(countries, regulations))

    return deps.templates.TemplateResponse(
        request=request,
        name='components/prompt_preview.html',
        context={
            'prompt_html': prompt_html,
            'selected_countries': countries,
            'selected_regulations': regulations,
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
            'is_executable': bool(countries or regulations),
            'reports': reports,
        },
    )


@router.get('/reports/{report_id}/download_csv')
async def download_csv(
    report_id: int,
    service: ReportService = Depends(get_report_service),
) -> StreamingResponse:
    """レポートデータをCSV形式でダウンロードする。

    Args:
        report_id: レポートID。
        service: レポートサービス。

    Returns:
        StreamingResponse: CSV形式のファイル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    headers, rows = await _get_report_data(report_id, service)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=result.csv'},
    )


@router.get('/reports/{report_id}/download_excel')
async def download_excel(
    report_id: int,
    service: ReportService = Depends(get_report_service),
) -> StreamingResponse:
    """レポートデータをExcel形式でダウンロードする。

    Args:
        report_id: レポートID。
        service: レポートサービス。

    Returns:
        StreamingResponse: Excel形式のファイル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    headers, rows = await _get_report_data(report_id, service)
    output = _create_excel_file(headers, rows)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=result.xlsx'},
    )

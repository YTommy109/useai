"""ページ表示に関連するルーター。"""

import csv
import io

import markdown
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.db.repository import CountryRepository, RegulationRepository, ReportRepository
from src.services.report_service import ReportService

router = APIRouter()
templates = Jinja2Templates(directory='src/templates')


async def _get_report_data(
    report_id: int, session: AsyncSession
) -> tuple[list[str], list[list[str]]]:
    """レポートデータを取得する。

    Args:
        report_id: レポートID。
        session: 非同期データベースセッション。

    Returns:
        tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    repo = ReportRepository(session)
    service = ReportService(repo, session)

    try:
        return await service.get_report_content(report_id)
    except ValueError as err:
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


@router.get('/', response_class=HTMLResponse)
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

    # レポート一覧を取得
    report_repo = ReportRepository(session)
    reports = await report_repo.get_all_desc()

    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': regulations,
            'reports': reports,
        },
    )


@router.post('/generate_document', response_class=HTMLResponse)
async def generate_document(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
    open_accordions: list[str] = Form(default=[]),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """選択された国と規制に基づいて文書を生成し、メインインターフェース全体を更新する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。
        open_accordions: 開いているアコーディオンのIDリスト。
        session: 非同期データベースセッション。

    Returns:
        HTMLResponse: 更新されたメインインターフェース。
    """
    country_repo = CountryRepository(session)
    regulation_repo = RegulationRepository(session)

    # 再レンダリングのために全データを取得
    grouped_countries = await country_repo.get_grouped_by_continent()
    all_regulations = await regulation_repo.get_all_names()

    # レポート一覧を取得
    report_repo = ReportRepository(session)
    reports = await report_repo.get_all_desc()

    return templates.TemplateResponse(
        request=request,
        name='components/main_interface.html',
        context={
            'grouped_countries': grouped_countries,
            'regulations': all_regulations,
            'selected_countries': countries,
            'selected_regulations': regulations,
            'open_accordions': open_accordions,
            'is_executable': bool(countries or regulations),
            'reports': reports,
            'prompt_html': markdown.markdown(
                ReportService.generate_prompt_text(countries, regulations)
            ),
        },
    )


@router.get('/reports/{report_id}/download_csv')
async def download_csv(
    report_id: int, session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    """レポートデータをCSV形式でダウンロードする。

    Args:
        report_id: レポートID。
        session: 非同期データベースセッション。

    Returns:
        StreamingResponse: CSV形式のファイル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    headers, rows = await _get_report_data(report_id, session)

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
    report_id: int, session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    """レポートデータをExcel形式でダウンロードする。

    Args:
        report_id: レポートID。
        session: 非同期データベースセッション。

    Returns:
        StreamingResponse: Excel形式のファイル。

    Raises:
        HTTPException: レポートが見つからない場合。
    """
    headers, rows = await _get_report_data(report_id, session)
    output = _create_excel_file(headers, rows)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=result.xlsx'},
    )

"""ページ表示に関連するルーター。"""

import csv
import io

import markdown
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.db.repository import CountryRepository, RegulationRepository, ReportRepository
from src.services.report_service import ReportService

router = APIRouter()
templates = Jinja2Templates(directory='src/templates')


def generate_dummy_data() -> tuple[list[str], list[list[str]]]:
    """ダミーデータを生成する。

    Returns:
        tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。
    """
    headers = [f'項目{i + 1}' for i in range(20)]
    rows = []
    for i in range(50):
        row = [f'データ{i + 1}-{j + 1}' for j in range(20)]
        # それっぽいデータを入れる
        row[2] = '適合' if i % 3 == 0 else '要確認'
        row[5] = 'あり' if i % 2 == 0 else 'なし'
        rows.append(row)
    return headers, rows


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


@router.post('/generate_table', response_class=HTMLResponse)
async def generate_table(request: Request) -> HTMLResponse:
    """ダミーのテーブルデータを生成する。

    Args:
        request: FastAPI リクエストオブジェクト。

    Returns:
        HTMLResponse: 生成されたテーブルを表示するレンダリングされたページ。
    """
    headers, rows = generate_dummy_data()

    return templates.TemplateResponse(
        request=request,
        name='table_result.html',
        context={
            'headers': headers,
            'rows': rows,
        },
    )


@router.get('/download_csv')
async def download_csv() -> StreamingResponse:
    """生成結果データをCSV形式でダウンロードする。

    Returns:
        StreamingResponse: CSV形式のファイル。
    """
    headers, rows = generate_dummy_data()

    # CSVデータを生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    # StreamingResponseで返す
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=result.csv'},
    )


@router.get('/download_excel')
async def download_excel() -> StreamingResponse:
    """生成結果データをExcel形式でダウンロードする。

    Returns:
        StreamingResponse: Excel形式のファイル。
    """
    headers, rows = generate_dummy_data()

    # Excelワークブックを作成
    wb = Workbook()
    ws = wb.active
    assert ws is not None  # type narrowing
    ws.title = '生成結果'

    # ヘッダーを書き込み
    ws.append(headers)

    # データを書き込み
    for row in rows:
        ws.append(row)

    # バイトストリームに保存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # StreamingResponseで返す
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=result.xlsx'},
    )

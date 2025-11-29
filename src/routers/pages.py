"""ページ表示に関連するルーター。"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.db.repository import CountryRepository, RegulationRepository

router = APIRouter()
templates = Jinja2Templates(directory='src/templates')


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

    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'grouped_countries': grouped_countries, 'regulations': regulations},
    )


@router.post('/generate_document', response_class=HTMLResponse)
async def generate_document(
    request: Request,
    countries: list[str] = Form(default=[]),
    regulations: list[str] = Form(default=[]),
) -> HTMLResponse:
    """選択された国と規制に基づいて文書を生成する。

    Args:
        request: FastAPI リクエストオブジェクト。
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。

    Returns:
        HTMLResponse: 生成された文書を表示するレンダリングされたページ。
    """
    return templates.TemplateResponse(
        request=request,
        name='document.html',
        context={
            'selected_countries': countries,
            'selected_regulations': regulations,
            'is_executable': bool(countries or regulations),
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
    # ダミーデータの生成 (20列 x 50行)
    headers = [f'項目{i + 1}' for i in range(20)]
    rows = []
    for i in range(50):
        row = [f'データ{i + 1}-{j + 1}' for j in range(20)]
        # それっぽいデータを入れる
        row[2] = '適合' if i % 3 == 0 else '要確認'
        row[5] = 'あり' if i % 2 == 0 else 'なし'
        rows.append(row)

    return templates.TemplateResponse(
        request=request,
        name='table_result.html',
        context={
            'headers': headers,
            'rows': rows,
        },
    )

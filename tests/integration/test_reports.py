import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Report, ReportStatus


@pytest.mark.asyncio
async def test_report_lifecycle(async_client: AsyncClient, session: AsyncSession) -> None:
    # 1. 初期状態: レポート一覧は空（または既存のもののみ）
    response = await async_client.get('/')
    assert response.status_code == 200
    assert 'レポート履歴' in response.text

    # 2. レポート作成 (POST /reports)
    payload = {'countries': ['Japan'], 'regulations': ['GDPR']}
    response = await async_client.post('/reports', data=payload)
    assert response.status_code == 200
    # レポート一覧が返ってくることを確認
    assert 'レポート履歴' in response.text

    # レポートが作成されたかDB確認
    result = await session.exec(select(Report))
    reports = result.all()
    assert len(reports) >= 1
    latest_report = reports[-1]
    assert latest_report.status == ReportStatus.COMPLETED

    # 3. レポート一覧取得 (GET /reports)
    response = await async_client.get('/reports')
    assert response.status_code == 200
    assert str(latest_report.id) in response.text
    assert ReportStatus.COMPLETED in response.text

    # 4. プレビュー取得 (GET /reports/{id}/preview)
    response = await async_client.get(f'/reports/{latest_report.id}/preview')
    assert response.status_code == 200
    assert 'プレビュー' in response.text
    assert '項目1' in response.text  # ダミーデータのヘッダー

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Report

# Fixtures are now in conftest.py


@pytest.mark.asyncio
async def test_メインページが表示される(client: TestClient) -> None:
    # Arrange
    # No specific arrangement needed beyond fixture setup

    # Act
    response = client.get('/')

    # Assert
    assert response.status_code == 200
    assert 'Test Country A' in response.text
    assert 'Test Country B' in response.text
    assert 'Test Regulation 1' in response.text
    assert 'Test Regulation 2' in response.text
    assert 'Test Regulation 2' in response.text


@pytest.mark.asyncio
async def test_国を選択してドキュメントを生成できる(client: TestClient) -> None:
    # Arrange
    payload = {'countries': ['Test Country A'], 'regulations': []}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'Test Country A' in response.text


@pytest.mark.asyncio
async def test_規制を選択してドキュメントを生成できる(client: TestClient) -> None:
    # Arrange
    payload = {'countries': [], 'regulations': ['Test Regulation 1']}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'Test Regulation 1' in response.text


@pytest.mark.asyncio
async def test_国と規制を両方選択してドキュメントを生成できる(client: TestClient) -> None:
    # Arrange
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # プロンプトデバッグエリアの確認
    debug_content = soup.find(id='prompt-debug-content')
    assert debug_content is not None
    assert 'ゴール: これはダミーのプロンプトです。' in debug_content.text
    assert 'Test Country A' in debug_content.text
    assert 'Test Regulation 1' in debug_content.text

    # 選択状態の維持を確認 (checked属性)
    country_checkbox = soup.find('input', {'value': 'Test Country A'})
    assert country_checkbox is not None
    assert country_checkbox.has_attr('checked')

    regulation_checkbox = soup.find('input', {'value': 'Test Regulation 1'})
    assert regulation_checkbox is not None
    assert regulation_checkbox.has_attr('checked')

    # 実行ボタンが有効化されていること
    execute_button = soup.find('button', {'id': 'execute-button'})
    assert execute_button is not None
    assert not execute_button.has_attr('disabled')


@pytest.mark.asyncio
async def test_何も選択しないと実行ボタンが無効になる(client: TestClient) -> None:
    # Arrange
    payload: dict[str, list[str]] = {'countries': [], 'regulations': []}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # 実行ボタンが無効化されていること
    execute_button = soup.find('button', {'id': 'execute-button'})
    assert execute_button is not None
    assert execute_button.has_attr('disabled')

    # プロンプトデバッグアコーディオンのチェックボックスが未チェックであること
    accordion_checkbox = soup.find('input', {'id': 'accordion-prompt-debug'})
    assert accordion_checkbox is not None
    assert not accordion_checkbox.has_attr('checked')


@pytest.mark.asyncio
async def test_アコーディオンの開閉状態が維持される(client: TestClient) -> None:
    # Arrange - アコーディオンを開いた状態で送信
    payload = {
        'countries': ['Test Country A'],
        'regulations': [],
        'open_accordions': ['prompt-debug'],
    }

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # アコーディオンのチェックボックスがチェックされていること
    accordion_checkbox = soup.find('input', {'id': 'accordion-prompt-debug'})
    assert accordion_checkbox is not None
    assert accordion_checkbox.has_attr('checked')

    # Arrange - アコーディオンを閉じた状態で送信
    payload_closed = {'countries': ['Test Country A'], 'regulations': [], 'open_accordions': []}

    # Act
    response_closed = client.post('/generate_document', data=payload_closed)

    # Assert
    assert response_closed.status_code == 200
    soup_closed = BeautifulSoup(response_closed.text, 'html.parser')

    # アコーディオンのチェックボックスが未チェックであること
    accordion_checkbox_closed = soup_closed.find('input', {'id': 'accordion-prompt-debug'})
    assert accordion_checkbox_closed is not None
    assert not accordion_checkbox_closed.has_attr('checked')


@pytest.mark.asyncio
async def test_テーブルを生成できる(client: TestClient, session: AsyncSession) -> None:
    # Arrange - レポートを作成
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}
    create_response = client.post('/reports', data=payload)
    assert create_response.status_code == 200

    # 作成されたレポートIDをデータベースから取得
    result = await session.exec(select(Report).order_by(col(Report.created_at).desc()))
    reports = list(result.all())
    assert len(reports) >= 1
    latest_report = reports[0]  # 最新のレポート（作成日時の降順で最初）
    report_id = latest_report.id
    assert report_id is not None

    # Act - プレビューを取得
    response = client.get(f'/reports/{report_id}/preview')

    # Assert
    assert response.status_code == 200
    assert '生成結果データ' in response.text
    assert '項目1' in response.text


@pytest.mark.asyncio
async def test_CSVダウンロードができる(client: TestClient, session: AsyncSession) -> None:
    # Arrange - レポートを作成
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}
    create_response = client.post('/reports', data=payload)
    assert create_response.status_code == 200

    # 作成されたレポートIDをデータベースから取得
    result = await session.exec(select(Report).order_by(col(Report.created_at).desc()))
    reports = list(result.all())
    assert len(reports) >= 1
    latest_report = reports[0]  # 最新のレポート（作成日時の降順で最初）
    report_id = latest_report.id
    assert report_id is not None

    # Act
    response = client.get(f'/reports/{report_id}/download_csv')

    # Assert
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/csv; charset=utf-8'
    assert 'attachment' in response.headers['content-disposition']
    assert 'filename=result.csv' in response.headers['content-disposition']

    # CSV内容の検証
    content = response.text
    assert '項目1' in content  # ヘッダーの確認
    assert 'データ1-1' in content  # データの確認


@pytest.mark.asyncio
async def test_Excelダウンロードができる(client: TestClient, session: AsyncSession) -> None:
    # Arrange - レポートを作成
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}
    create_response = client.post('/reports', data=payload)
    assert create_response.status_code == 200

    # 作成されたレポートIDをデータベースから取得
    result = await session.exec(select(Report).order_by(col(Report.created_at).desc()))
    reports = list(result.all())
    assert len(reports) >= 1
    latest_report = reports[0]  # 最新のレポート（作成日時の降順で最初）
    report_id = latest_report.id
    assert report_id is not None

    # Act
    response = client.get(f'/reports/{report_id}/download_excel')

    # Assert
    assert response.status_code == 200
    assert (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        in response.headers['content-type']
    )
    assert 'attachment' in response.headers['content-disposition']
    assert 'filename=result.xlsx' in response.headers['content-disposition']

    # Excelファイルとして読み込めることを確認
    assert len(response.content) > 0

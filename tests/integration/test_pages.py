import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
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
    # メインページはレポート履歴ページなので、レポート履歴の要素を確認
    assert 'レポート履歴' in response.text
    assert 'No.' in response.text
    assert '作成日時' in response.text


@pytest.mark.parametrize(
    ('countries', 'regulations', 'expected_texts'),
    [
        (['Test Country A'], [], ['Test Country A']),
        ([], ['Test Regulation 1'], ['Test Regulation 1']),
        (['Test Country A'], ['Test Regulation 1'], ['Test Country A', 'Test Regulation 1']),
    ],
)
async def test_ドキュメント生成_選択項目が反映される(
    client: TestClient,
    countries: list[str],
    regulations: list[str],
    expected_texts: list[str],
) -> None:
    # Arrange
    payload = {'countries': countries, 'regulations': regulations}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    for text in expected_texts:
        assert text in response.text


@pytest.mark.asyncio
async def test_プロンプトプレビューが表示される(client: TestClient) -> None:
    # Arrange
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}

    # Act
    response = client.post('/preview_prompt', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'Test Country A' in response.text
    assert 'Test Regulation 1' in response.text
    assert 'プロンプト' in response.text


@pytest.mark.asyncio
async def test_テーブルを生成できる(client: TestClient, completed_report: Report) -> None:
    # Arrange
    report_id = completed_report.id
    assert report_id is not None

    # Act
    response = client.get(f'/reports/{report_id}/preview')

    # Assert
    assert response.status_code == 200
    assert 'プレビュー' in response.text
    assert '項目1' in response.text


@pytest.mark.asyncio
async def test_CSVダウンロードができる(client: TestClient, completed_report: Report) -> None:
    # Arrange
    report_id = completed_report.id
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
    assert '項目1' in content
    assert 'データ1-1' in content


@pytest.mark.asyncio
async def test_Excelダウンロードができる(client: TestClient, completed_report: Report) -> None:
    # Arrange
    report_id = completed_report.id
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
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_レポート一覧が表示される(client: TestClient, session: AsyncSession) -> None:
    # Arrange - レポートを作成
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}
    client.post('/reports', data=payload)

    # Act
    response = client.get('/reports')

    # Assert
    assert response.status_code == 200
    assert 'レポート履歴' in response.text
    # 作成したレポートが表示されているか確認（厳密なIDチェックは省略するが、行が存在することを確認）
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select('tbody tr')
    assert len(rows) >= 1


@pytest.mark.asyncio
async def test_レポート作成_国も法規も選択しないとバリデーションエラー(client: TestClient) -> None:
    # Arrange
    payload: dict[str, list[str]] = {'countries': [], 'regulations': []}

    # Act
    response = client.post('/reports', data=payload)

    # Assert
    assert response.status_code == 422
    assert '国または法規を選択してください' in response.text


@pytest.mark.parametrize(
    'endpoint_template',
    [
        '/reports/{id}/preview',
        '/reports/{id}/download_csv',
        '/reports/{id}/download_excel',
    ],
)
@pytest.mark.asyncio
async def test_存在しないレポートへのアクセスは404(
    client: TestClient, endpoint_template: str
) -> None:
    # Arrange
    non_existent_id = 99999
    endpoint = endpoint_template.format(id=non_existent_id)

    # Act
    response = client.get(endpoint)

    # Assert
    assert response.status_code == 404
    assert 'Report not found' in response.text


@pytest.mark.asyncio
async def test_main_interfaceエンドポイントが動作する(client: TestClient) -> None:
    # Act
    response = client.get('/main_interface')

    # Assert
    assert response.status_code == 200
    assert '国を選択' in response.text
    assert '法規を選択' in response.text
    assert 'プロンプト' in response.text
    assert '実行' in response.text


@pytest.mark.asyncio
async def test_ホームページに新規作成ボタンがある(client: TestClient) -> None:
    # Act
    response = client.get('/')

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # 新規作成ボタンが存在すること
    buttons = soup.find_all('button')
    new_report_button = next(
        (btn for btn in buttons if btn.string and '新規作成' in btn.string), None
    )
    assert new_report_button is not None

    # 動的エリアが存在すること
    dynamic_area = soup.find(id='dynamic-area')
    assert dynamic_area is not None

    # プロンプトプレビュー用モーダルが存在すること
    modal = soup.find(id='prompt-preview-modal')
    assert modal is not None

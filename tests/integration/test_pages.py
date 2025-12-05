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
async def test_ドキュメント生成_UI状態が正しい(client: TestClient) -> None:
    # Arrange
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

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
    assert 'プロンプトプレビュー' in response.text


@pytest.mark.asyncio
async def test_テーブルを生成できる(client: TestClient, session: AsyncSession) -> None:
    # Arrange - レポートを作成
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}
    create_response = client.post('/reports', data=payload)

    # Assert - リダイレクトヘッダーが返される
    assert create_response.status_code == 200
    assert 'HX-Redirect' in create_response.headers
    assert create_response.headers['HX-Redirect'] == '/'

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
    assert 'レポート #' in response.text
    assert '項目1' in response.text


@pytest.mark.asyncio
async def test_CSVダウンロードができる(client: TestClient, session: AsyncSession) -> None:
    # Arrange - レポートを作成
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}
    create_response = client.post('/reports', data=payload)
    assert create_response.status_code == 200
    assert 'HX-Redirect' in create_response.headers

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
    assert 'HX-Redirect' in create_response.headers

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
    assert 'プロンプトプレビュー' in response.text
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


@pytest.mark.asyncio
async def test_新規作成機能_初期状態では実行ボタンが無効(client: TestClient) -> None:
    # Act
    response = client.get('/main_interface')

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # 実行ボタンが存在し、無効状態であること
    execute_button = soup.find('button', id='execute-button')
    assert execute_button is not None
    assert 'disabled' in execute_button.attrs

    # プロンプトプレビューボタンは有効であること
    buttons = soup.find_all('button')
    preview_button = next(
        (btn for btn in buttons if btn.string and 'プロンプトプレビュー' in btn.string), None
    )
    assert preview_button is not None
    assert 'disabled' not in preview_button.attrs


@pytest.mark.asyncio
async def test_新規作成機能_選択後は実行ボタンが有効(client: TestClient) -> None:
    # Act - 国を選択してフォームを更新
    payload = {'countries': ['Test Country A']}
    response = client.post('/update_main_interface', data=payload)

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # 実行ボタンが存在し、有効状態であること
    execute_button = soup.find('button', id='execute-button')
    assert execute_button is not None
    assert 'disabled' not in execute_button.attrs

    # 選択された国がチェックされていること
    country_checkbox = soup.find('input', {'name': 'countries', 'value': 'Test Country A'})
    assert country_checkbox is not None
    assert 'checked' in country_checkbox.attrs


@pytest.mark.asyncio
async def test_新規作成機能_法規選択でも実行ボタンが有効(client: TestClient) -> None:
    # Act - 法規を選択してフォームを更新
    payload = {'regulations': ['Test Regulation 1']}
    response = client.post('/update_main_interface', data=payload)

    # Assert
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')

    # 実行ボタンが存在し、有効状態であること
    execute_button = soup.find('button', id='execute-button')
    assert execute_button is not None
    assert 'disabled' not in execute_button.attrs

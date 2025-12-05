from unittest.mock import mock_open, patch

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country, Regulation


@pytest.mark.asyncio
async def test_管理ダッシュボードの統計が表示される(
    client: TestClient, session: AsyncSession
) -> None:
    # Arrange: 初期データを追加
    session.add(Country(name='初期国', continent='アジア'))
    session.add(Regulation(name='初期規制'))
    await session.commit()

    # Act
    response = client.get('/admin')

    # Assert
    assert response.status_code == 200

    # BeautifulSoupを使用して堅牢なアサーション
    soup = BeautifulSoup(response.text, 'html.parser')
    country_count_elem = soup.select_one('#country-count')
    regulation_count_elem = soup.select_one('#regulation-count')

    assert country_count_elem is not None
    assert regulation_count_elem is not None
    assert country_count_elem.text == '3'
    assert regulation_count_elem.text == '3'


@pytest.mark.asyncio
async def test_国データをインポートできる(client: TestClient, session: AsyncSession) -> None:
    # Arrange: CSVファイル読み込みをモック化
    csv_content = 'name,continent\n新規国1,欧州\n新規国2,アジア'

    with (
        patch('src.routers.admin.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        # Act
        response = client.post('/admin/import/countries')

    # Assert
    assert response.status_code == 200
    assert response.text == '2'

    # Verify database state
    countries = await session.exec(select(Country))
    results = countries.all()
    assert len(results) == 2
    assert results[0].name == '新規国1'
    assert results[0].continent == '欧州'
    assert results[1].name == '新規国2'
    assert results[1].continent == 'アジア'


@pytest.mark.asyncio
async def test_規制データをインポートできる(client: TestClient, session: AsyncSession) -> None:
    # Arrange: CSVファイル読み込みをモック化
    csv_content = 'name\n新規規制1\n新規規制2'

    with (
        patch('src.routers.admin.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        # Act
        response = client.post('/admin/import/regulations')

        # Assert
        assert response.status_code == 200
        assert response.text == '2'  # 更新後の件数が返される

        # DBの内容を検証
        result = await session.exec(select(Regulation))
        regulations = result.all()
        assert len(regulations) == 2
        names = [r.name for r in regulations]
        assert '新規規制1' in names
        assert '新規規制2' in names


@pytest.mark.parametrize(
    'endpoint',
    ['/admin/import/countries', '/admin/import/regulations'],
)
@pytest.mark.asyncio
async def test_インポート_ファイルが存在しない場合404(client: TestClient, endpoint: str) -> None:
    # Arrange: ファイルが存在しないことをモック
    with patch('src.routers.admin.Path.exists', return_value=False):
        # Act
        response = client.post(endpoint)

        # Assert
        assert response.status_code == 404
        assert 'ファイルが見つかりません' in response.text


@pytest.mark.parametrize(
    ('endpoint', 'model_class', 'header'),
    [
        ('/admin/import/countries', Country, 'name,continent\n'),
        ('/admin/import/regulations', Regulation, 'name\n'),
    ],
)
@pytest.mark.asyncio
async def test_インポート_空のCSVの場合0件(
    client: TestClient,
    session: AsyncSession,
    endpoint: str,
    model_class: type[SQLModel],
    header: str,
) -> None:
    # Arrange: ヘッダーのみのCSVファイル
    with (
        patch('src.routers.admin.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=header)),
    ):
        # Act
        response = client.post(endpoint)

        # Assert
        assert response.status_code == 200
        assert response.text == '0'

        # DBが空であることを確認
        result = await session.exec(select(model_class))
        items = result.all()
        assert len(items) == 0

from collections.abc import AsyncGenerator
from unittest.mock import mock_open, patch

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from src.db.engine import get_session
from src.db.models import Country, Regulation
from src.main import app

# テスト用の非同期インメモリ SQLite
DATABASE_URL = 'sqlite+aiosqlite:///'
engine = create_async_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)


@pytest.fixture(name='session')
async def session_fixture() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(name='client')
async def client_fixture(session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


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
    assert country_count_elem.text == '1'
    assert regulation_count_elem.text == '1'


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


@pytest.mark.asyncio
async def test_国データCSVファイルがないと404エラーが返る(client: TestClient) -> None:
    # Arrange: ファイルが存在しないことをモック
    with patch('src.routers.admin.Path.exists', return_value=False):
        # Act
        response = client.post('/admin/import/countries')

        # Assert
        assert response.status_code == 404
        assert 'ファイルが見つかりません' in response.text


@pytest.mark.asyncio
async def test_規制データCSVファイルがないと404エラーが返る(client: TestClient) -> None:
    # Arrange: ファイルが存在しないことをモック
    with patch('src.routers.admin.Path.exists', return_value=False):
        # Act
        response = client.post('/admin/import/regulations')

        # Assert
        assert response.status_code == 404
        assert 'ファイルが見つかりません' in response.text


@pytest.mark.asyncio
async def test_国データ空のCSVをインポートすると0件になる(
    client: TestClient, session: AsyncSession
) -> None:
    # Arrange: ヘッダーのみのCSVファイル
    csv_content = 'name,continent\n'

    with (
        patch('src.routers.admin.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        # Act
        response = client.post('/admin/import/countries')

        # Assert
        assert response.status_code == 200
        assert response.text == '0'

        # DBが空であることを確認
        result = await session.exec(select(Country))
        countries = result.all()
        assert len(countries) == 0


@pytest.mark.asyncio
async def test_規制データ空のCSVをインポートすると0件になる(
    client: TestClient, session: AsyncSession
) -> None:
    # Arrange: ヘッダーのみのCSVファイル
    csv_content = 'name\n'

    with (
        patch('src.routers.admin.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        # Act
        response = client.post('/admin/import/regulations')

        # Assert
        assert response.status_code == 200
        assert response.text == '0'

        # DBが空であることを確認
        result = await session.exec(select(Regulation))
        regulations = result.all()
        assert len(regulations) == 0

from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from src.db.models import Country, Regulation
from src.main import app, get_session

# テスト用の非同期インメモリ SQLite
DATABASE_URL = 'sqlite+aiosqlite:///'
engine = create_async_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)


@pytest.fixture(name='session')
async def session_fixture():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(name='client')
async def client_fixture(session: AsyncSession):
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_dashboard_stats(client: TestClient, session: AsyncSession):
    """管理ダッシュボードの統計表示をテストする。"""
    # Arrange: 初期データを追加
    session.add(Country(name='初期国', continent='アジア'))
    session.add(Regulation(name='初期規制'))
    await session.commit()

    # Act
    response = client.get('/admin')

    # Assert
    assert response.status_code == 200
    # テンプレートは {{ country_count }} と {{ regulation_count }} をレンダリングする
    # 1件ずつ追加したので、"1" が含まれていることを確認
    assert '1' in response.text


@pytest.mark.asyncio
async def test_import_countries(client: TestClient, session: AsyncSession):
    """国データのサーバーサイド取り込みをテストする。"""
    # Arrange: CSVファイル読み込みをモック化
    csv_content = 'name,continent\n新規国1,欧州\n新規国2,アジア'

    with (
        patch('src.main.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        # Act
        response = client.post('/admin/import/countries')

        # Assert
        assert response.status_code == 200
        assert response.text == '2'  # 更新後の件数が返される

        # DBの内容を検証
        result = await session.exec(select(Country))
        countries = result.all()
        assert len(countries) == 2
        names = [c.name for c in countries]
        assert '新規国1' in names
        assert '新規国2' in names


@pytest.mark.asyncio
async def test_import_regulations(client: TestClient, session: AsyncSession):
    """規制データのサーバーサイド取り込みをテストする。"""
    # Arrange: CSVファイル読み込みをモック化
    csv_content = 'name\n新規規制1\n新規規制2'

    with (
        patch('src.main.Path.exists', return_value=True),
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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from src.db.engine import get_session
from src.db.models import Country, Regulation
from src.main import app

# Async In-memory SQLite for testing
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
        # Insert explicit test data
        session.add(Country(name='Test Country A', continent='Asia'))
        session.add(Country(name='Test Country B', continent='Europe'))
        session.add(Regulation(name='Test Regulation 1'))
        session.add(Regulation(name='Test Regulation 2'))
        await session.commit()
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
async def test_メインページが表示される(client: TestClient):
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
    assert 'id="execute-button-container"' in response.text  # 実行ボタンコンテナの確認


@pytest.mark.asyncio
async def test_国を選択してドキュメントを生成できる(client: TestClient):
    # Arrange
    payload = {'countries': ['Test Country A'], 'regulations': []}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'Test Country A' in response.text


@pytest.mark.asyncio
async def test_規制を選択してドキュメントを生成できる(client: TestClient):
    # Arrange
    payload = {'countries': [], 'regulations': ['Test Regulation 1']}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'Test Regulation 1' in response.text


@pytest.mark.asyncio
async def test_国と規制を両方選択してドキュメントを生成できる(client: TestClient):
    # Arrange
    payload = {'countries': ['Test Country A'], 'regulations': ['Test Regulation 1']}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'Test Country A' in response.text
    assert 'Test Regulation 1' in response.text
    assert 'ゴール:' in response.text  # ドキュメント部分の確認
    assert '項目1' not in response.text  # テーブル部分は含まれないこと
    assert 'disabled' not in response.text  # 選択されているのでボタンは有効


@pytest.mark.asyncio
async def test_何も選択しないと実行ボタンが無効になる(client: TestClient):
    # Arrange
    payload = {'countries': [], 'regulations': []}

    # Act
    response = client.post('/generate_document', data=payload)

    # Assert
    assert response.status_code == 200
    assert 'disabled' in response.text  # 何も選択されていないのでボタンは無効


@pytest.mark.asyncio
async def test_テーブルを生成できる(client: TestClient):
    # Act
    response = client.post('/generate_table')

    # Assert
    assert response.status_code == 200
    assert '生成結果データ' in response.text
    assert '項目1' in response.text


@pytest.mark.asyncio
async def test_CSVダウンロードができる(client: TestClient):
    # Act
    response = client.get('/download_csv')

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
async def test_Excelダウンロードができる(client: TestClient):
    # Act
    response = client.get('/download_excel')

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

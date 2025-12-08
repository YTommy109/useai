from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from src.db.engine import get_session
from src.db.models import Country, Regulation
from src.dependencies import get_report_service
from src.main import app
from src.repositories import ReportRepository
from src.services.llm_service import LLMService
from src.services.report_service import ReportService

# Async In-memory SQLite for testing
DATABASE_URL = 'sqlite+aiosqlite:///'
engine = create_async_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)


@pytest.fixture(name='session')
async def session_fixture() -> AsyncGenerator[AsyncSession, None]:
    """非同期データベースセッションフィクスチャ。"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Insert explicit test data (common for pages tests)
        session.add(Country(name='Test Country A', continent='Asia'))
        session.add(Country(name='Test Country B', continent='Europe'))
        session.add(Regulation(name='Test Regulation 1'))
        session.add(Regulation(name='Test Regulation 2'))
        await session.commit()
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(name='async_client')
async def async_client_fixture(
    session: AsyncSession, tmp_path: Path
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """非同期HTTPクライアントフィクスチャ。"""

    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    def get_report_service_override() -> ReportService:
        """テスト用のReportServiceを返す（tmp_pathを使用）。"""
        repository = ReportRepository(session)
        # LLMサービスをモック化
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_tsv.return_value = (
            ['項目1', '項目2', '項目3'],
            [
                ['データ1-1', 'データ1-2', 'データ1-3'],
                ['データ2-1', 'データ2-2', 'データ2-3'],
            ],
        )
        return ReportService(repository, session, mock_llm_service, base_dir=str(tmp_path))

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_report_service] = get_report_service_override
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url='http://test'
    ) as client:  # Changed to httpx.AsyncClient
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name='client')
def client_fixture(session: AsyncSession, tmp_path: Path) -> Generator[TestClient, None, None]:
    """同期HTTPクライアントフィクスチャ。"""

    # TestClient for synchronous tests (or async tests using TestClient)
    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    def get_report_service_override() -> ReportService:
        """テスト用のReportServiceを返す（tmp_pathを使用）。"""
        repository = ReportRepository(session)
        # LLMサービスをモック化
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_tsv.return_value = (
            ['項目1', '項目2', '項目3'],
            [
                ['データ1-1', 'データ1-2', 'データ1-3'],
                ['データ2-1', 'データ2-2', 'データ2-3'],
            ],
        )
        return ReportService(repository, session, mock_llm_service, base_dir=str(tmp_path))

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_report_service] = get_report_service_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

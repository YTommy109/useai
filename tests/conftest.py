import csv
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
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
from src.db.models import Country, Regulation, Report, ReportStatus
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


class TestReportService(ReportService):
    """テスト用のReportService（テスト用エンジンを使用）。"""

    async def process_report_async(self, report_id: int, prompt: str) -> None:
        """レポートのLLM処理を非同期で実行する（テスト用エンジンを使用）。"""
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as bg_session:
            try:
                bg_repository = ReportRepository(bg_session)
                bg_service = ReportService(
                    bg_repository, bg_session, self.llm_service, self.base_dir
                )
                bg_report = await bg_repository.get_by_id(report_id)
                if not bg_report:
                    return
                await self._process_report_with_session(bg_service, bg_report, prompt, bg_session)
            except Exception:
                await bg_session.rollback()
                raise


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


def _create_mock_llm_service() -> AsyncMock:
    """モックLLMサービスを作成する。"""
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_tsv.return_value = (
        ['項目1', '項目2', '項目3'],
        [
            ['データ1-1', 'データ1-2', 'データ1-3'],
            ['データ2-1', 'データ2-2', 'データ2-3'],
        ],
    )
    return mock_llm_service


def _create_report_service_override(session: AsyncSession, tmp_path: Path) -> ReportService:
    """テスト用のReportServiceを返す（tmp_pathを使用）。"""
    repository = ReportRepository(session)
    mock_llm_service = _create_mock_llm_service()
    return TestReportService(repository, session, mock_llm_service, base_dir=str(tmp_path))


@pytest.fixture(name='completed_report')
async def completed_report_fixture(session: AsyncSession, tmp_path: Path) -> Report:
    """完了状態のレポートを作成するフィクスチャ。"""
    report_dir = tmp_path / '20230101_000000'
    report_dir.mkdir(parents=True, exist_ok=True)

    # prompt.txtを作成
    (report_dir / 'prompt.txt').write_text('Test Prompt', encoding='utf-8')

    # result.tsvを作成
    with open(report_dir / 'result.tsv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['項目1', '項目2', '項目3'])
        writer.writerow(['データ1-1', 'データ1-2', 'データ1-3'])
        writer.writerow(['データ2-1', 'データ2-2', 'データ2-3'])

    # レポートレコードを作成
    report = Report(
        created_at=datetime.now(UTC).replace(tzinfo=None),
        status=ReportStatus.COMPLETED,
        directory_path=str(report_dir),
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


@pytest.fixture(name='async_client')
async def async_client_fixture(
    session: AsyncSession, tmp_path: Path
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """非同期HTTPクライアントフィクスチャ。"""

    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_report_service] = lambda: _create_report_service_override(
        session, tmp_path
    )
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name='client')
def client_fixture(session: AsyncSession, tmp_path: Path) -> Generator[TestClient, None, None]:
    """同期HTTPクライアントフィクスチャ。"""

    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_report_service] = lambda: _create_report_service_override(
        session, tmp_path
    )
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

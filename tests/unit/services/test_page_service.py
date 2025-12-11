"""PageService の単体テスト。"""

from unittest.mock import AsyncMock

import pytest

from src.db.models import Report, ReportStatus
from src.repositories import CountryRepository, RegulationRepository, ReportRepository
from src.services.page_service import PageService


@pytest.fixture
def mock_country_repo() -> AsyncMock:
    return AsyncMock(spec=CountryRepository)


@pytest.fixture
def mock_regulation_repo() -> AsyncMock:
    return AsyncMock(spec=RegulationRepository)


@pytest.fixture
def mock_report_repo() -> AsyncMock:
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def service(
    mock_country_repo: AsyncMock,
    mock_regulation_repo: AsyncMock,
    mock_report_repo: AsyncMock,
) -> PageService:
    return PageService(mock_country_repo, mock_regulation_repo, mock_report_repo)


@pytest.mark.asyncio
async def test_get_main_page_dataが正しいデータを返す(
    service: PageService,
    mock_country_repo: AsyncMock,
    mock_regulation_repo: AsyncMock,
    mock_report_repo: AsyncMock,
) -> None:
    # Arrange
    grouped_countries = {'アジア': ['日本', '中国'], '欧州': ['フランス', 'ドイツ']}
    regulations = ['GDPR', 'CCPA']
    reports = [
        Report(
            id=1,
            created_at=None,
            status=ReportStatus.COMPLETED,
            directory_path='/path/to/report1',
        ),
        Report(
            id=2,
            created_at=None,
            status=ReportStatus.PROCESSING,
            directory_path='/path/to/report2',
        ),
    ]

    mock_country_repo.get_grouped_by_continent.return_value = grouped_countries
    mock_regulation_repo.get_all_names.return_value = regulations
    mock_report_repo.get_all_desc.return_value = reports

    # Act
    (
        result_grouped_countries,
        result_regulations,
        result_reports,
    ) = await service.get_main_page_data()

    # Assert
    assert result_grouped_countries == grouped_countries
    assert result_regulations == regulations
    assert result_reports == reports

    mock_country_repo.get_grouped_by_continent.assert_called_once()
    mock_regulation_repo.get_all_names.assert_called_once()
    mock_report_repo.get_all_desc.assert_called_once()


@pytest.mark.asyncio
async def test_get_main_page_dataが空のデータでも動作する(
    service: PageService,
    mock_country_repo: AsyncMock,
    mock_regulation_repo: AsyncMock,
    mock_report_repo: AsyncMock,
) -> None:
    # Arrange
    mock_country_repo.get_grouped_by_continent.return_value = {}
    mock_regulation_repo.get_all_names.return_value = []
    mock_report_repo.get_all_desc.return_value = []

    # Act
    (
        result_grouped_countries,
        result_regulations,
        result_reports,
    ) = await service.get_main_page_data()

    # Assert
    assert result_grouped_countries == {}
    assert result_regulations == []
    assert result_reports == []

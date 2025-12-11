"""GetReportsUseCase の単体テスト。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.db.models import Report, ReportStatus
from src.repositories import ReportRepository
from src.usecases.get_reports import GetReportsUseCase


@pytest.fixture
def mock_report_repository() -> AsyncMock:
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def usecase(mock_report_repository: AsyncMock) -> GetReportsUseCase:
    return GetReportsUseCase(mock_report_repository)


@pytest.mark.asyncio
async def test_executeがレポート一覧と処理中フラグを返す(
    usecase: GetReportsUseCase,
    mock_report_repository: AsyncMock,
) -> None:
    # Arrange
    reports = [
        Report(
            id=1,
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            status=ReportStatus.PROCESSING,
            directory_path='/path/to/report1',
        ),
        Report(
            id=2,
            created_at=datetime(2023, 1, 2, 0, 0, 0),
            status=ReportStatus.COMPLETED,
            directory_path='/path/to/report2',
        ),
    ]
    mock_report_repository.get_all_desc.return_value = reports

    # Act
    result_reports, has_processing = await usecase.execute()

    # Assert
    assert result_reports == reports
    assert has_processing is True
    mock_report_repository.get_all_desc.assert_called_once()


@pytest.mark.asyncio
async def test_executeが処理中レポートがない場合にFalseを返す(
    usecase: GetReportsUseCase,
    mock_report_repository: AsyncMock,
) -> None:
    # Arrange
    reports = [
        Report(
            id=1,
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            status=ReportStatus.COMPLETED,
            directory_path='/path/to/report1',
        ),
        Report(
            id=2,
            created_at=datetime(2023, 1, 2, 0, 0, 0),
            status=ReportStatus.COMPLETED,
            directory_path='/path/to/report2',
        ),
    ]
    mock_report_repository.get_all_desc.return_value = reports

    # Act
    result_reports, has_processing = await usecase.execute()

    # Assert
    assert result_reports == reports
    assert has_processing is False


@pytest.mark.asyncio
async def test_executeが空のリストでも動作する(
    usecase: GetReportsUseCase,
    mock_report_repository: AsyncMock,
) -> None:
    # Arrange
    mock_report_repository.get_all_desc.return_value = []

    # Act
    result_reports, has_processing = await usecase.execute()

    # Assert
    assert result_reports == []
    assert has_processing is False

"""ReportRepository の単体テスト。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
import pytest_mock

from src.db.models import Report, ReportStatus
from src.repositories.report_repository import ReportRepository


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repository(mock_session: AsyncMock) -> ReportRepository:
    return ReportRepository(mock_session)


@pytest.mark.asyncio
async def test_get_all_descが作成日時の降順でレポートを返す(
    repository: ReportRepository,
    mocker: pytest_mock.MockerFixture,
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
            created_at=datetime(2023, 1, 3, 0, 0, 0),
            status=ReportStatus.COMPLETED,
            directory_path='/path/to/report2',
        ),
        Report(
            id=3,
            created_at=datetime(2023, 1, 2, 0, 0, 0),
            status=ReportStatus.COMPLETED,
            directory_path='/path/to/report3',
        ),
    ]

    # BaseRepository.get_all() をモック
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = reports

    # Act
    result = await repository.get_all_desc()

    # Assert
    assert len(result) == 3
    assert result[0].id == 2  # 最新のレポート
    assert result[1].id == 3
    assert result[2].id == 1  # 最古のレポート
    mock_get_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_descが空のリストでも動作する(
    repository: ReportRepository,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = []

    # Act
    result = await repository.get_all_desc()

    # Assert
    assert result == []
    mock_get_all.assert_called_once()

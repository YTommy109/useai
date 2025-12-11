"""RegulationRepository の単体テスト。"""

from unittest.mock import AsyncMock

import pytest
import pytest_mock

from src.db.models import Regulation
from src.repositories.regulation_repository import RegulationRepository


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repository(mock_session: AsyncMock) -> RegulationRepository:
    return RegulationRepository(mock_session)


@pytest.mark.asyncio
async def test_get_all_namesが規制名のリストを返す(
    repository: RegulationRepository,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    regulations = [
        Regulation(id=1, name='GDPR'),
        Regulation(id=2, name='CCPA'),
        Regulation(id=3, name='PIPEDA'),
    ]

    # BaseRepository.get_all() をモック
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = regulations

    # Act
    result = await repository.get_all_names()

    # Assert
    assert result == ['GDPR', 'CCPA', 'PIPEDA']
    mock_get_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_namesが空のリストでも動作する(
    repository: RegulationRepository,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = []

    # Act
    result = await repository.get_all_names()

    # Assert
    assert result == []
    mock_get_all.assert_called_once()

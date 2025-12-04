"""RegulationService の単体テスト。"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from src.db.repository import RegulationRepository
from src.db.service import RegulationService


@pytest.mark.asyncio
async def test_CSVファイルからのインポートが成功する() -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_repo.delete_all = AsyncMock()
    mock_repo.count = AsyncMock(return_value=2)

    mock_session = AsyncMock()
    mock_session.add = Mock()  # add() は同期メソッド
    service = RegulationService(mock_repo, mock_session)

    csv_content = 'name\n規制A\n規制B'

    # Act
    with (
        patch('src.db.service.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        count = await service.import_from_csv(Path('dummy.csv'))

    # Assert
    assert count == 2
    mock_repo.delete_all.assert_called_once()
    mock_session.commit.assert_called_once()
    assert mock_session.add.call_count == 2


@pytest.mark.asyncio
async def test_CSVファイルが存在しない場合FileNotFoundErrorが発生する() -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_session = AsyncMock()
    service = RegulationService(mock_repo, mock_session)

    # Act & Assert
    with (
        patch('src.db.service.Path.exists', return_value=False),
        pytest.raises(FileNotFoundError, match='CSV file not found'),
    ):
        await service.import_from_csv(Path('nonexistent.csv'))


@pytest.mark.asyncio
async def test_空のCSVファイルの場合0件が返される() -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_repo.delete_all = AsyncMock()
    mock_repo.count = AsyncMock(return_value=0)

    mock_session = AsyncMock()
    mock_session.add = Mock()  # add() は同期メソッド
    service = RegulationService(mock_repo, mock_session)

    csv_content = 'name\n'

    # Act
    with (
        patch('src.db.service.Path.exists', return_value=True),
        patch('builtins.open', mock_open(read_data=csv_content)),
    ):
        count = await service.import_from_csv(Path('empty.csv'))

    # Assert
    assert count == 0
    mock_repo.delete_all.assert_called_once()
    mock_session.commit.assert_called_once()
    assert mock_session.add.call_count == 0

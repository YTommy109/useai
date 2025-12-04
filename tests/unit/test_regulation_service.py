"""RegulationService の単体テスト。"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_mock

from src.db.repository import RegulationRepository
from src.db.service import RegulationService


@pytest.mark.asyncio
async def test_CSVファイルからのインポートが成功する(mocker: pytest_mock.MockerFixture) -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_repo.delete_all = AsyncMock()
    mock_repo.count = AsyncMock(return_value=2)

    mock_session = AsyncMock()
    mock_session.add = Mock()  # add() は同期メソッド
    service = RegulationService(mock_repo, mock_session)

    csv_content = 'name\n規制A\n規制B'

    # Act
    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'exists', return_value=True)
    # 外部モジュール（builtins）は patch を使用
    mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))

    count = await service.import_from_csv(Path('dummy.csv'))

    # Assert
    assert count == 2
    mock_repo.delete_all.assert_called_once()
    mock_session.commit.assert_called_once()
    assert mock_session.add.call_count == 2


@pytest.mark.asyncio
async def test_CSVファイルが存在しない場合FileNotFoundErrorが発生する(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_session = AsyncMock()
    service = RegulationService(mock_repo, mock_session)

    # Act & Assert
    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'exists', return_value=False)

    with pytest.raises(FileNotFoundError, match='CSV file not found'):
        await service.import_from_csv(Path('nonexistent.csv'))


@pytest.mark.asyncio
async def test_空のCSVファイルの場合0件が返される(mocker: pytest_mock.MockerFixture) -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_repo.delete_all = AsyncMock()
    mock_repo.count = AsyncMock(return_value=0)

    mock_session = AsyncMock()
    mock_session.add = Mock()  # add() は同期メソッド
    service = RegulationService(mock_repo, mock_session)

    csv_content = 'name\n'

    # Act
    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'exists', return_value=True)
    # 外部モジュール（builtins）は patch を使用
    mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))

    count = await service.import_from_csv(Path('empty.csv'))

    # Assert
    assert count == 0
    mock_repo.delete_all.assert_called_once()
    mock_session.commit.assert_called_once()
    assert mock_session.add.call_count == 0


@pytest.mark.asyncio
async def test_不正なCSV形式の場合KeyErrorが発生する(mocker: pytest_mock.MockerFixture) -> None:
    # Arrange
    mock_repo = Mock(spec=RegulationRepository)
    mock_repo.delete_all = AsyncMock()

    mock_session = AsyncMock()
    mock_session.add = Mock()  # add() は同期メソッド
    service = RegulationService(mock_repo, mock_session)

    # カラムが不足しているCSV
    csv_content = 'invalid_column\n規制A\n規制B'

    # Act & Assert
    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'exists', return_value=True)
    # 外部モジュール（builtins）は patch を使用
    mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))

    with pytest.raises(KeyError, match='name'):
        await service.import_from_csv(Path('invalid.csv'))

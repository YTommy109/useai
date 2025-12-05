"""CountryService の単体テスト。"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_mock

from src.db.repository import CountryRepository
from src.services.country_service import CountryService


@pytest.mark.asyncio
async def test_CSVファイルからのインポートが成功する(mocker: pytest_mock.MockerFixture) -> None:
    # Arrange
    mock_repo = Mock(spec=CountryRepository)
    mock_repo.delete_all = AsyncMock()
    mock_repo.count = AsyncMock(return_value=2)

    mock_session = AsyncMock()
    mock_session.add = Mock()  # add() は同期メソッド
    service = CountryService(mock_repo, mock_session)

    csv_content = 'name,continent\n国A,アジア\n国B,欧州'

    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'exists', return_value=True)
    # 外部モジュール（builtins）は patch を使用
    mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))

    # Act
    count = await service.import_from_csv(Path('dummy.csv'))

    # Assert
    assert count == 2
    mock_repo.delete_all.assert_called_once()
    mock_session.commit.assert_called_once()
    assert mock_session.add.call_count == 2


@pytest.mark.parametrize(
    ('file_exists', 'csv_content', 'expected_exception', 'match_message'),
    [
        (False, '', FileNotFoundError, 'CSV file not found'),
        (True, 'name\n国A\n国B', KeyError, 'continent'),
    ],
)
async def test_インポート_エラー系(
    mocker: pytest_mock.MockerFixture,
    file_exists: bool,
    csv_content: str,
    expected_exception: type[Exception],
    match_message: str,
) -> None:
    # Arrange
    mock_repo = Mock(spec=CountryRepository)
    mock_session = AsyncMock()
    service = CountryService(mock_repo, mock_session)

    mocker.patch.object(Path, 'exists', return_value=file_exists)
    mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))

    # Act & Assert

    with pytest.raises(expected_exception, match=match_message):
        await service.import_from_csv(Path('dummy.csv'))

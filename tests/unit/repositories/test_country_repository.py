"""CountryRepository の単体テスト。"""

from unittest.mock import AsyncMock

import pytest
import pytest_mock

from src.db.models import Country
from src.repositories.country_repository import CountryRepository


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repository(mock_session: AsyncMock) -> CountryRepository:
    return CountryRepository(mock_session)


@pytest.mark.asyncio
async def test_get_all_namesが国名のリストを返す(
    repository: CountryRepository,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    countries = [
        Country(id=1, name='日本', continent='アジア'),
        Country(id=2, name='アメリカ', continent='北米'),
        Country(id=3, name='フランス', continent='欧州'),
    ]

    # BaseRepository.get_all() をモック
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = countries

    # Act
    result = await repository.get_all_names()

    # Assert
    assert result == ['日本', 'アメリカ', 'フランス']
    mock_get_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_namesが空のリストでも動作する(
    repository: CountryRepository,
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


@pytest.mark.asyncio
async def test_get_grouped_by_continentが大陸別にグループ化された国名を返す(
    repository: CountryRepository,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    countries = [
        Country(id=1, name='日本', continent='アジア'),
        Country(id=2, name='中国', continent='アジア'),
        Country(id=3, name='フランス', continent='欧州'),
        Country(id=4, name='ドイツ', continent='欧州'),
        Country(id=5, name='アメリカ', continent='北米'),
    ]

    # BaseRepository.get_all() をモック
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = countries

    # Act
    result = await repository.get_grouped_by_continent()

    # Assert
    assert result == {
        'アジア': ['日本', '中国'],
        '欧州': ['フランス', 'ドイツ'],
        '北米': ['アメリカ'],
    }
    mock_get_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_grouped_by_continentが空のリストでも動作する(
    repository: CountryRepository,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Arrange
    mock_get_all = mocker.patch.object(repository, 'get_all', new_callable=AsyncMock)
    mock_get_all.return_value = []

    # Act
    result = await repository.get_grouped_by_continent()

    # Assert
    assert result == {}
    mock_get_all.assert_called_once()

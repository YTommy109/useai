from datetime import datetime
from pathlib import Path

import pytest

from src.db.models import Report, ReportStatus
from src.services.report_service import ReportService


@pytest.fixture
def mock_repo(mocker):
    return mocker.AsyncMock()


@pytest.fixture
def mock_session(mocker):
    return mocker.AsyncMock()


@pytest.fixture
def service(mock_repo, mock_session):
    return ReportService(mock_repo, mock_session)


@pytest.mark.asyncio
async def test_レポート作成が成功する(service, mock_repo, mock_session, mocker):
    # Arrange
    prompt = 'Test Prompt'
    countries = ['Country A']
    regulations = ['Regulation B']

    mock_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.PROCESSING,
        directory_path='data/reports/20230101_000000',
    )
    mock_repo.create.return_value = mock_report
    mock_repo.update.return_value = mock_report  # updateの戻り値を設定

    # 外部モジュールは patch を使用
    mock_datetime = mocker.patch('src.services.report_service.datetime')
    mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)

    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'mkdir')

    # 外部モジュール（builtins）は patch を使用
    mock_file = mocker.patch('builtins.open', mocker.mock_open())

    # Act
    result = await service.create_report(prompt, countries, regulations)

    # Assert
    assert result == mock_report
    mock_repo.create.assert_called_once()
    assert mock_file.call_count >= 2  # prompt.txt and result.tsv
    mock_repo.update.assert_called_once()
    assert mock_repo.update.call_args[0][0].status == ReportStatus.COMPLETED


@pytest.mark.asyncio
async def test_レポート内容の取得が成功する(service, mock_repo, mocker):
    # Arrange
    report_id = 1
    mock_report = Report(
        id=report_id,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.COMPLETED,
        directory_path='data/reports/20230101_000000',
    )
    mock_repo.get_by_id.return_value = mock_report

    tsv_content = 'header1\theader2\nval1\tval2'

    # 内部モジュール（Path）は patch.object を使用
    mocker.patch.object(Path, 'exists', return_value=True)

    # 外部モジュール（builtins）は patch を使用
    mocker.patch('builtins.open', mocker.mock_open(read_data=tsv_content))

    # Act
    headers, rows = await service.get_report_content(report_id)

    # Assert
    assert headers == ['header1', 'header2']
    assert rows == [['val1', 'val2']]
    mock_repo.get_by_id.assert_called_with(report_id)

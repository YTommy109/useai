from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_mock

from src.db.models import Report, ReportStatus
from src.services.report_service import ReportService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_repo: AsyncMock, mock_session: AsyncMock, tmp_path: Path) -> ReportService:
    return ReportService(mock_repo, mock_session, base_dir=str(tmp_path))


@pytest.mark.asyncio
async def test_レポート作成が成功する(
    service: ReportService,
    mock_repo: AsyncMock,
    mock_session: AsyncMock,
    mocker: pytest_mock.MockerFixture,
    tmp_path: Path,
) -> None:
    # Arrange
    prompt = 'Test Prompt'

    # tmp_pathを使用したディレクトリパス
    timestamp = '20230101_000000'
    directory_path = f'{tmp_path}/{timestamp}'

    mock_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.PROCESSING,
        directory_path=directory_path,
    )
    mock_repo.create.return_value = mock_report
    mock_repo.update.return_value = mock_report  # updateの戻り値を設定

    # テスト対象モジュール内でimportされているものは patch を使用（文字列パス）
    mock_datetime = mocker.patch('src.services.report_service.datetime')
    mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)

    # テストファイルでimport済みのクラスは patch.object を使用（オブジェクト参照）
    mocker.patch.object(Path, 'mkdir')

    # builtinsは文字列パスでアクセス
    mock_file = mocker.patch('builtins.open', mocker.mock_open())

    # Act
    result = await service.create_report(prompt)

    # Assert
    assert result == mock_report
    mock_repo.create.assert_called_once()
    assert mock_file.call_count >= 2  # prompt.txt and result.tsv
    mock_repo.update.assert_called_once()
    assert mock_repo.update.call_args[0][0].status == ReportStatus.COMPLETED


@pytest.mark.asyncio
async def test_レポート内容の取得が成功する(
    service: ReportService,
    mock_repo: AsyncMock,
    mocker: pytest_mock.MockerFixture,
    tmp_path: Path,
) -> None:
    # Arrange
    report_id = 1
    directory_path = f'{tmp_path}/20230101_000000'

    mock_report = Report(
        id=report_id,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.COMPLETED,
        directory_path=directory_path,
    )
    mock_repo.get_by_id.return_value = mock_report

    tsv_content = 'header1\theader2\nval1\tval2'

    # テストファイルでimport済みのクラスは patch.object を使用（オブジェクト参照）
    mocker.patch.object(Path, 'exists', return_value=True)

    # builtinsは文字列パスでアクセス
    mocker.patch('builtins.open', mocker.mock_open(read_data=tsv_content))

    # Act
    headers, rows = await service.get_report_content(report_id)

    # Assert
    assert headers == ['header1', 'header2']
    assert rows == [['val1', 'val2']]
    mock_repo.get_by_id.assert_called_with(report_id)


@pytest.mark.asyncio
async def test_レポート作成時にファイル保存が失敗するとステータスがFAILEDになる(
    service: ReportService,
    mock_repo: AsyncMock,
    mock_session: AsyncMock,
    mocker: pytest_mock.MockerFixture,
    tmp_path: Path,
) -> None:
    # Arrange
    prompt = 'Test Prompt'
    timestamp = '20230101_000000'
    directory_path = f'{tmp_path}/{timestamp}'

    mock_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.PROCESSING,
        directory_path=directory_path,
    )
    mock_repo.create.return_value = mock_report
    mock_repo.update.return_value = mock_report

    # テスト対象モジュール内でimportされているものは patch を使用（文字列パス）
    mock_datetime = mocker.patch('src.services.report_service.datetime')
    mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)

    # テストファイルでimport済みのクラスは patch.object を使用（オブジェクト参照）
    mocker.patch.object(Path, 'mkdir', side_effect=OSError('Permission denied'))

    # Act & Assert
    with pytest.raises(OSError, match='Permission denied'):
        await service.create_report(prompt)

    # ステータスがFAILEDに更新されたことを確認
    assert mock_repo.update.call_count == 1
    assert mock_repo.update.call_args[0][0].status == ReportStatus.FAILED
    mock_session.rollback.assert_called_once()
    assert mock_session.commit.call_count == 2  # レコード作成時とステータス更新時


@pytest.mark.asyncio
async def test_レポート未存在時にget_report_contentがValueErrorを発生させる(
    service: ReportService, mock_repo: AsyncMock
) -> None:
    # Arrange
    report_id = 999
    mock_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match='Report not found'):
        await service.get_report_content(report_id)

    mock_repo.get_by_id.assert_called_with(report_id)

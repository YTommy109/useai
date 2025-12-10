from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_mock

from src.db.models import Report, ReportStatus
from src.exceptions import InvalidFilePathError, ResourceNotFoundError
from src.services.llm_service import LLMService
from src.services.report_service import ReportService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_llm_service() -> AsyncMock:
    return AsyncMock(spec=LLMService)


@pytest.fixture
def service(
    mock_repo: AsyncMock,
    mock_session: AsyncMock,
    mock_llm_service: AsyncMock,
    tmp_path: Path,
) -> ReportService:
    return ReportService(mock_repo, mock_session, mock_llm_service, base_dir=str(tmp_path))


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
async def test_レポート未存在時にget_report_contentがResourceNotFoundErrorを発生させる(
    service: ReportService, mock_repo: AsyncMock
) -> None:
    # Arrange
    report_id = 999
    mock_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Report not found'):
        await service.get_report_content(report_id)

    mock_repo.get_by_id.assert_called_with(report_id)


@pytest.mark.asyncio
async def test_レポートレコードを作成できる(
    service: ReportService,
    mock_repo: AsyncMock,
    mock_session: AsyncMock,
    tmp_path: Path,
) -> None:
    # Arrange
    prompt = 'Test prompt content'
    prompt_name = 'prompt_1_1'
    mock_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.PROCESSING,
        directory_path=f'{tmp_path}/20230101_000000',
        prompt_name=prompt_name,
    )
    mock_repo.create.return_value = mock_report

    # Act
    result = await service.create_report_record(prompt, prompt_name)

    # Assert
    assert result == mock_report
    mock_repo.create.assert_called_once()
    mock_session.commit.assert_called_once()
    # prompt.txtが保存されていることを確認
    report_dir = Path(mock_report.directory_path)
    assert (report_dir / 'prompt.txt').exists()
    assert (report_dir / 'prompt.txt').read_text(encoding='utf-8') == prompt


@pytest.mark.asyncio
async def test_パストラバーサル攻撃を防げる(
    service: ReportService,
    mock_repo: AsyncMock,
    tmp_path: Path,
) -> None:
    # Arrange
    report_id = 1
    # base_dirの外側を指すパス
    malicious_path = str(tmp_path.parent / 'malicious' / '20230101_000000')
    mock_report = Report(
        id=report_id,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.COMPLETED,
        directory_path=malicious_path,
    )
    mock_repo.get_by_id.return_value = mock_report

    # Act & Assert
    with pytest.raises(InvalidFilePathError):
        await service.get_report_content(report_id)

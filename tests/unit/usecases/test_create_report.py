"""CreateReportUseCase の単体テスト。"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks

from src.db.models import Report, ReportStatus
from src.exceptions import ValidationError
from src.repositories import ReportRepository
from src.services.prompt_service import PromptService
from src.services.report_service import ReportService
from src.usecases.create_report import CreateReportUseCase


@pytest.fixture
def mock_report_service() -> AsyncMock:
    return AsyncMock(spec=ReportService)


@pytest.fixture
def mock_report_repository() -> AsyncMock:
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def mock_prompt_service() -> Mock:
    return Mock(spec=PromptService)


@pytest.fixture
def background_tasks() -> BackgroundTasks:
    return BackgroundTasks()


@pytest.fixture
def usecase(
    mock_report_service: AsyncMock,
    mock_report_repository: AsyncMock,
    mock_prompt_service: Mock,
    background_tasks: BackgroundTasks,
) -> CreateReportUseCase:
    return CreateReportUseCase(
        mock_report_service,
        mock_report_repository,
        mock_prompt_service,
        background_tasks,
    )


@pytest.mark.asyncio
async def test_executeがレポートを作成して返す(
    usecase: CreateReportUseCase,
    mock_report_service: AsyncMock,
    mock_report_repository: AsyncMock,
    mock_prompt_service: Mock,
    background_tasks: BackgroundTasks,
) -> None:
    # Arrange
    countries = ['日本', 'アメリカ']
    regulations = ['GDPR', 'CCPA']
    prompt = 'Generated prompt'
    prompt_name = 'prompt_1_1'

    mock_prompt_service.generate_first_prompt.return_value = prompt
    mock_prompt_service.get_prompt_name.return_value = prompt_name

    created_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.PROCESSING,
        directory_path='/path/to/report',
        prompt_name=prompt_name,
    )
    mock_report_service.create_report_record.return_value = created_report

    existing_reports = [
        Report(
            id=1,
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            status=ReportStatus.PROCESSING,
            directory_path='/path/to/report',
        ),
    ]
    mock_report_repository.get_all_desc.return_value = existing_reports

    # Act
    reports, has_processing = await usecase.execute(countries, regulations)

    # Assert
    assert reports == existing_reports
    assert has_processing is True
    mock_prompt_service.generate_first_prompt.assert_called_once_with(countries, regulations)
    mock_prompt_service.get_prompt_name.assert_called_once()
    mock_report_service.create_report_record.assert_called_once_with(prompt, prompt_name)
    mock_report_repository.get_all_desc.assert_called_once()


@pytest.mark.asyncio
async def test_executeが国のみ選択された場合にレポートを作成する(
    usecase: CreateReportUseCase,
    mock_report_service: AsyncMock,
    mock_report_repository: AsyncMock,
    mock_prompt_service: Mock,
) -> None:
    # Arrange
    countries = ['日本']
    regulations: list[str] = []
    prompt = 'Generated prompt'
    prompt_name = 'prompt_1_1'

    mock_prompt_service.generate_first_prompt.return_value = prompt
    mock_prompt_service.get_prompt_name.return_value = prompt_name

    created_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.COMPLETED,
        directory_path='/path/to/report',
        prompt_name=prompt_name,
    )
    mock_report_service.create_report_record.return_value = created_report

    existing_reports = [created_report]
    mock_report_repository.get_all_desc.return_value = existing_reports

    # Act
    reports, has_processing = await usecase.execute(countries, regulations)

    # Assert
    assert reports == existing_reports
    assert has_processing is False


@pytest.mark.asyncio
async def test_executeが規制のみ選択された場合にレポートを作成する(
    usecase: CreateReportUseCase,
    mock_report_service: AsyncMock,
    mock_report_repository: AsyncMock,
    mock_prompt_service: Mock,
) -> None:
    # Arrange
    countries: list[str] = []
    regulations = ['GDPR']
    prompt = 'Generated prompt'
    prompt_name = 'prompt_1_1'

    mock_prompt_service.generate_first_prompt.return_value = prompt
    mock_prompt_service.get_prompt_name.return_value = prompt_name

    created_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.COMPLETED,
        directory_path='/path/to/report',
        prompt_name=prompt_name,
    )
    mock_report_service.create_report_record.return_value = created_report

    existing_reports = [created_report]
    mock_report_repository.get_all_desc.return_value = existing_reports

    # Act
    reports, has_processing = await usecase.execute(countries, regulations)

    # Assert
    assert reports == existing_reports
    assert has_processing is False


@pytest.mark.asyncio
async def test_executeが国も規制も選択されていない場合にValidationErrorを発生させる(
    usecase: CreateReportUseCase,
) -> None:
    # Arrange
    countries: list[str] = []
    regulations: list[str] = []

    # Act & Assert
    with pytest.raises(ValidationError, match='国または法規を選択してください'):
        await usecase.execute(countries, regulations)


@pytest.mark.asyncio
async def test_executeがバックグラウンドタスクを追加する(
    usecase: CreateReportUseCase,
    mock_report_service: AsyncMock,
    mock_report_repository: AsyncMock,
    mock_prompt_service: Mock,
    background_tasks: BackgroundTasks,
) -> None:
    # Arrange
    countries = ['日本']
    regulations = ['GDPR']
    prompt = 'Generated prompt'
    prompt_name = 'prompt_1_1'

    mock_prompt_service.generate_first_prompt.return_value = prompt
    mock_prompt_service.get_prompt_name.return_value = prompt_name

    created_report = Report(
        id=1,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        status=ReportStatus.PROCESSING,
        directory_path='/path/to/report',
        prompt_name=prompt_name,
    )
    mock_report_service.create_report_record.return_value = created_report

    existing_reports = [created_report]
    mock_report_repository.get_all_desc.return_value = existing_reports

    # Act
    await usecase.execute(countries, regulations)

    # Assert
    # バックグラウンドタスクが追加されていることを確認
    # BackgroundTasks の内部実装に依存しないため、process_report_async が呼ばれることを確認
    assert len(background_tasks.tasks) > 0

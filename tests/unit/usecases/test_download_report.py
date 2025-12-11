"""DownloadReportUseCase の単体テスト。"""

import io
from unittest.mock import AsyncMock, Mock

import pytest

from src.exceptions import ResourceNotFoundError
from src.services.export_service import ExportService
from src.services.report_service import ReportService
from src.usecases.download_report import DownloadReportUseCase


@pytest.fixture
def mock_report_service() -> AsyncMock:
    return AsyncMock(spec=ReportService)


@pytest.fixture
def mock_export_service() -> Mock:
    return Mock(spec=ExportService)


@pytest.fixture
def usecase(mock_report_service: AsyncMock, mock_export_service: Mock) -> DownloadReportUseCase:
    return DownloadReportUseCase(mock_report_service, mock_export_service)


@pytest.mark.asyncio
async def test_get_report_dataがレポートデータを取得する(
    usecase: DownloadReportUseCase,
    mock_report_service: AsyncMock,
) -> None:
    # Arrange
    report_id = 1
    headers = ['header1', 'header2']
    rows = [['val1', 'val2'], ['val3', 'val4']]

    mock_report_service.get_report_content.return_value = (headers, rows)

    # Act
    result_headers, result_rows = await usecase.get_report_data(report_id)

    # Assert
    assert result_headers == headers
    assert result_rows == rows
    mock_report_service.get_report_content.assert_called_once_with(report_id)


@pytest.mark.asyncio
async def test_get_report_dataがレポートが見つからない場合にResourceNotFoundErrorを発生させる(
    usecase: DownloadReportUseCase,
    mock_report_service: AsyncMock,
) -> None:
    # Arrange
    report_id = 999
    mock_report_service.get_report_content.side_effect = ResourceNotFoundError('Report', '999')

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Report'):
        await usecase.get_report_data(report_id)


@pytest.mark.asyncio
async def test_create_csvがCSVファイルを作成する(
    usecase: DownloadReportUseCase,
    mock_report_service: AsyncMock,
    mock_export_service: Mock,
) -> None:
    # Arrange
    report_id = 1
    headers = ['header1', 'header2']
    rows = [['val1', 'val2']]

    mock_report_service.get_report_content.return_value = (headers, rows)

    csv_output = io.StringIO()
    csv_output.write('header1,header2\r\nval1,val2\r\n')
    csv_output.seek(0)
    mock_export_service.create_csv.return_value = csv_output

    # Act
    result = await usecase.create_csv(report_id)

    # Assert
    assert isinstance(result, io.StringIO)
    mock_report_service.get_report_content.assert_called_once_with(report_id)
    mock_export_service.create_csv.assert_called_once_with(headers, rows)


@pytest.mark.asyncio
async def test_create_excelがExcelファイルを作成する(
    usecase: DownloadReportUseCase,
    mock_report_service: AsyncMock,
    mock_export_service: Mock,
) -> None:
    # Arrange
    report_id = 1
    headers = ['header1', 'header2']
    rows = [['val1', 'val2']]

    mock_report_service.get_report_content.return_value = (headers, rows)

    excel_output = io.BytesIO()
    excel_output.write(b'fake excel content')
    excel_output.seek(0)
    mock_export_service.create_excel.return_value = excel_output

    # Act
    result = await usecase.create_excel(report_id)

    # Assert
    assert isinstance(result, io.BytesIO)
    mock_report_service.get_report_content.assert_called_once_with(report_id)
    mock_export_service.create_excel.assert_called_once_with(headers, rows)


@pytest.mark.asyncio
async def test_create_csvがレポートが見つからない場合にResourceNotFoundErrorを発生させる(
    usecase: DownloadReportUseCase,
    mock_report_service: AsyncMock,
) -> None:
    # Arrange
    report_id = 999
    mock_report_service.get_report_content.side_effect = ResourceNotFoundError('Report', '999')

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Report'):
        await usecase.create_csv(report_id)


@pytest.mark.asyncio
async def test_create_excelがレポートが見つからない場合にResourceNotFoundErrorを発生させる(
    usecase: DownloadReportUseCase,
    mock_report_service: AsyncMock,
) -> None:
    # Arrange
    report_id = 999
    mock_report_service.get_report_content.side_effect = ResourceNotFoundError('Report', '999')

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Report'):
        await usecase.create_excel(report_id)

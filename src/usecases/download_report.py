"""レポートダウンロードユースケース。"""

import io

from src.exceptions import ResourceNotFoundError
from src.services.export_service import ExportService
from src.services.report_service import ReportService


class DownloadReportUseCase:
    """レポートダウンロードユースケース。"""

    def __init__(
        self,
        report_service: ReportService,
        export_service: ExportService,
    ) -> None:
        """初期化。

        Args:
            report_service: レポートサービス。
            export_service: エクスポートサービス。
        """
        self.report_service = report_service
        self.export_service = export_service

    async def get_report_data(self, report_id: int) -> tuple[list[str], list[list[str]]]:
        """レポートデータを取得する。

        Args:
            report_id: レポートID。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。

        Raises:
            ResourceNotFoundError: レポートが見つからない場合。
        """
        try:
            return await self.report_service.get_report_content(report_id)
        except ResourceNotFoundError as err:
            raise ResourceNotFoundError('Report', str(report_id)) from err

    async def create_csv(self, report_id: int) -> io.StringIO:
        """CSVファイルを作成する。

        Args:
            report_id: レポートID。

        Returns:
            io.StringIO: CSV形式の文字列ストリーム。

        Raises:
            ResourceNotFoundError: レポートが見つからない場合。
        """
        headers, rows = await self.get_report_data(report_id)
        return self.export_service.create_csv(headers, rows)

    async def create_excel(self, report_id: int) -> io.BytesIO:
        """Excelファイルを作成する。

        Args:
            report_id: レポートID。

        Returns:
            io.BytesIO: Excelファイルのバイトストリーム。

        Raises:
            ResourceNotFoundError: レポートが見つからない場合。
        """
        headers, rows = await self.get_report_data(report_id)
        return self.export_service.create_excel(headers, rows)

"""レポート一覧取得ユースケース。"""

from src.db.models import Report, ReportStatus
from src.repositories import ReportRepository


class GetReportsUseCase:
    """レポート一覧取得ユースケース。"""

    def __init__(self, report_repository: ReportRepository) -> None:
        """初期化。

        Args:
            report_repository: レポートリポジトリ。
        """
        self.report_repository = report_repository

    async def execute(self) -> tuple[list[Report], bool]:
        """レポート一覧を取得する。

        Returns:
            tuple[list[Report], bool]: レポート一覧と処理中フラグ。
        """
        reports = await self.report_repository.get_all_desc()
        has_processing = any(r.status == ReportStatus.PROCESSING for r in reports)
        return reports, has_processing

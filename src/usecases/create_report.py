"""レポート作成ユースケース。"""

from fastapi import BackgroundTasks

from src.db.models import Report, ReportStatus
from src.exceptions import ValidationError
from src.repositories import ReportRepository
from src.services.prompt_service import PromptService
from src.services.report_service import ReportService


class CreateReportUseCase:
    """レポート作成ユースケース。"""

    def __init__(
        self,
        report_service: ReportService,
        report_repository: ReportRepository,
        prompt_service: PromptService,
        background_tasks: BackgroundTasks,
    ) -> None:
        """初期化。

        Args:
            report_service: レポートサービス。
            report_repository: レポートリポジトリ。
            prompt_service: プロンプトサービス。
            background_tasks: バックグラウンドタスク。
        """
        self.report_service = report_service
        self.report_repository = report_repository
        self.prompt_service = prompt_service
        self.background_tasks = background_tasks

    async def execute(
        self, countries: list[str], regulations: list[str]
    ) -> tuple[list[Report], bool]:
        """レポートを作成する。

        Args:
            countries: 選択された国名のリスト。
            regulations: 選択された規制名のリスト。

        Returns:
            tuple[list[Report], bool]: レポート一覧と処理中フラグ。

        Raises:
            ValidationError: 国または法規が選択されていない場合。
        """
        # バリデーション
        if not countries and not regulations:
            raise ValidationError('国または法規を選択してください')

        # プロンプト生成
        prompt = self.prompt_service.generate_first_prompt(countries, regulations)
        prompt_name = self.prompt_service.get_prompt_name()

        # レポートレコード作成
        report = await self.report_service.create_report_record(prompt, prompt_name)

        # バックグラウンドタスク追加
        if report.id is not None:
            self.background_tasks.add_task(
                self.report_service.process_report_async, report.id, prompt
            )

        # レポート一覧取得
        reports = await self.report_repository.get_all_desc()
        has_processing = any(r.status == ReportStatus.PROCESSING for r in reports)

        return reports, has_processing

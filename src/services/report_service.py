import csv
import random
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Report, ReportStatus
from src.db.repository import ReportRepository


class ReportService:
    """レポートサービス。"""

    def __init__(self, repository: ReportRepository, session: AsyncSession) -> None:
        """初期化。

        Args:
            repository: レポートリポジトリ。
            session: 非同期データベースセッション。
        """
        self.repository = repository
        self.session = session

    async def create_report(
        self, prompt: str, countries: list[str], regulations: list[str]
    ) -> Report:
        """レポートを作成する。

        Args:
            prompt: プロンプト。
            countries: 選択された国名のリスト。
            regulations: 選択された規制名のリスト。

        Returns:
            Report: 作成されたレポート。
        """
        # TODO: 将来的に使用するため、引数は保持するが現在は使用しない
        _ = countries
        _ = regulations

        now = datetime.now(UTC)
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        directory_path = f'data/reports/{timestamp}'

        # DBにprocessing状態で保存
        report = Report(
            created_at=now,
            status=ReportStatus.PROCESSING,
            directory_path=directory_path,
        )
        report = await self.repository.create(report)

        try:
            self._save_report_files(directory_path, prompt)
            await self._update_status(report, ReportStatus.COMPLETED)
        except Exception:
            await self._update_status(report, ReportStatus.FAILED)
            raise

        return report

    async def _update_status(self, report: Report, status: ReportStatus) -> None:
        """レポートのステータスを更新する。"""
        report.status = status
        await self.repository.update(report)

    def _save_report_files(self, directory_path: str, prompt: str) -> None:
        """レポートファイルを保存する。

        Args:
            directory_path: 保存先ディレクトリパス。
            prompt: プロンプト。
        """
        # ディレクトリ作成
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)

        # prompt.txt保存
        with open(path / 'prompt.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)

        # ダミーデータ生成
        headers, rows = self._generate_dummy_data()

        # result.tsv保存
        with open(path / 'result.tsv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(headers)
            writer.writerows(rows)

    async def get_report_content(self, report_id: int) -> tuple[list[str], list[list[str]]]:
        """レポートの内容を取得する。

        Args:
            report_id: レポートID。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。
        """
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise ValueError(f'Report not found: {report_id}')

        path = Path(report.directory_path) / 'result.tsv'
        if not path.exists():
            return [], []

        with open(path, encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
            if not rows:
                return [], []
            headers = rows[0]
            data = rows[1:]
            return headers, data

    def _generate_dummy_data(self) -> tuple[list[str], list[list[str]]]:
        """ダミーデータを生成する。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。
        """
        headers = [f'項目{i + 1}' for i in range(20)]
        rows = []
        for i in range(50):
            row = [f'データ{i + 1}-{j + 1}' for j in range(20)]
            # それっぽいデータを入れる
            row[2] = random.choice(['適合', '要確認', '不適合', '保留'])  # noqa: S311
            row[5] = random.choice(['あり', 'なし', '不明'])  # noqa: S311
            row[8] = str(random.randint(1, 100))  # noqa: S311
            row[12] = random.choice(['A', 'B', 'C', 'D', 'E'])  # noqa: S311
            rows.append(row)
        return headers, rows

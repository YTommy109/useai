import csv
import random
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Report, ReportStatus
from src.db.repository import ReportRepository


class ReportService:
    """レポートサービス。"""

    def __init__(
        self,
        repository: ReportRepository,
        session: AsyncSession,
        base_dir: str = 'data/reports',
    ) -> None:
        """初期化。

        Args:
            repository: レポートリポジトリ。
            session: 非同期データベースセッション。
            base_dir: レポートファイルの保存先ベースディレクトリ。
        """
        self.repository = repository
        self.session = session
        self.base_dir = base_dir

    @staticmethod
    def generate_prompt_text(countries: list[str], regulations: list[str]) -> str:
        """プロンプトテキストを生成する。

        Args:
            countries: 選択された国名のリスト。
            regulations: 選択された規制名のリスト。

        Returns:
            str: 生成されたプロンプトテキスト。
        """
        prompt_lines = [
            'ゴール: これはダミーのプロンプトです。',
            '',
            'ヘッダー部: プロンプトヘッダー部です。',
            '',
            '条件部:',
            '国:',
        ]
        for country in countries:
            prompt_lines.append(f'- {country}')

        prompt_lines.append('')
        prompt_lines.append('法規:')
        for regulation in regulations:
            prompt_lines.append(f'- {regulation}')

        prompt_lines.append('')
        prompt_lines.append('詳細: ここは詳細が入ります。')

        return '\n'.join(prompt_lines)

    async def create_report(self, prompt: str) -> Report:
        """レポートを作成する。

        Args:
            prompt: プロンプト。

        Returns:
            Report: 作成されたレポート。
        """
        report = await self._create_report_record()
        await self.session.commit()

        try:
            self._save_report_files(report.directory_path, prompt)
            await self._update_status(report, ReportStatus.COMPLETED)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            await self._update_status(report, ReportStatus.FAILED)
            await self.session.commit()
            raise

        return report

    async def _create_report_record(self) -> Report:
        """レポートレコードを作成する。

        Returns:
            Report: 作成されたレポートレコード。
        """
        # UTC時刻を取得
        now_utc = datetime.now(UTC)

        # ディレクトリ名はJST（日本標準時）で作成
        now_jst = now_utc.astimezone(ZoneInfo('Asia/Tokyo'))
        timestamp = now_jst.strftime('%Y%m%d_%H%M%S')
        directory_path = f'{self.base_dir}/{timestamp}'

        # データベースにはタイムゾーン情報なしのUTC時刻を保存
        # （SQLiteはタイムゾーン情報を保持しないため、UTC時刻として扱う）
        report = Report(
            created_at=now_utc.replace(tzinfo=None),
            status=ReportStatus.PROCESSING,
            directory_path=directory_path,
        )
        return await self.repository.create(report)

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
        headers, rows = ReportService.generate_dummy_data()

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

    @staticmethod
    def generate_dummy_data() -> tuple[list[str], list[list[str]]]:
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

import csv
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import settings
from src.db.engine import engine
from src.db.models import Report, ReportStatus
from src.exceptions import InvalidFilePathError, ResourceNotFoundError
from src.repositories import ReportRepository
from src.services.llm_service import LLMService


class ReportService:
    """レポートサービス。"""

    def __init__(
        self,
        repository: ReportRepository,
        session: AsyncSession,
        llm_service: LLMService | None = None,
        base_dir: str | None = None,
    ) -> None:
        """初期化。

        Args:
            repository: レポートリポジトリ。
            session: 非同期データベースセッション。
            llm_service: LLMサービス。Noneの場合は新規作成。
            base_dir: レポートファイルの保存先ベースディレクトリ。Noneの場合は設定から取得。
        """
        self.repository = repository
        self.session = session
        self.llm_service = llm_service or LLMService()
        self.base_dir = base_dir or settings.report_base_dir

    async def create_report_record(self, prompt: str, prompt_name: str | None = None) -> Report:
        """レポートレコードを作成する（LLM処理は別途実行）。

        Args:
            prompt: プロンプト（保存用）。
            prompt_name: プロンプト名。

        Returns:
            Report: 作成されたレポートレコード。
        """
        report = await self._create_report_record(prompt_name)
        await self.session.commit()

        # プロンプトファイルを先に保存
        path = Path(report.directory_path)
        path.mkdir(parents=True, exist_ok=True)
        prompt_filename = self._get_prompt_filename(prompt_name)
        with open(path / prompt_filename, 'w', encoding='utf-8') as f:
            f.write(prompt)

        return report

    async def process_report_async(self, report_id: int, prompt: str) -> None:
        """レポートのLLM処理を非同期で実行する。

        Args:
            report_id: レポートID。
            prompt: プロンプト。
        """
        # 新しいセッションを作成
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            try:
                # 新しいサービスインスタンスを作成
                repository = ReportRepository(session)
                service = ReportService(repository, session, self.llm_service, self.base_dir)

                report = await repository.get_by_id(report_id)
                if not report:
                    return

                await self._process_report_with_session(service, report, prompt, session)
            except Exception:
                await session.rollback()
                raise

    async def _process_report_with_session(
        self, service: 'ReportService', report: Report, prompt: str, session: AsyncSession
    ) -> None:
        """セッションを使用してレポートを処理する。

        Args:
            service: レポートサービス。
            report: レポート。
            prompt: プロンプト。
            session: データベースセッション。
        """
        try:
            await service._save_report_files(report.directory_path, prompt, report.prompt_name)
            await service._update_status(report, ReportStatus.COMPLETED)
            await session.commit()
        except Exception:
            await session.rollback()
            await service._update_status(report, ReportStatus.FAILED)
            await session.commit()
            raise

    async def _create_report_record(self, prompt_name: str | None = None) -> Report:
        """レポートレコードを作成する。

        Args:
            prompt_name: プロンプト名。

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
            prompt_name=prompt_name,
        )
        return await self.repository.create(report)

    async def _update_status(self, report: Report, status: ReportStatus) -> None:
        """レポートのステータスを更新する。"""
        report.status = status
        await self.repository.update(report)

    async def _save_report_files(
        self, directory_path: str, prompt: str, prompt_name: str | None = None
    ) -> None:
        """レポートファイルを保存する。

        Args:
            directory_path: 保存先ディレクトリパス。
            prompt: プロンプト。
            prompt_name: プロンプト名。
        """
        # ディレクトリ作成
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)

        # プロンプトファイル保存
        prompt_filename = self._get_prompt_filename(prompt_name)
        with open(path / prompt_filename, 'w', encoding='utf-8') as f:
            f.write(prompt)

        # LLMからTSVデータを生成
        headers, rows = await self.llm_service.generate_tsv(prompt)

        # 結果TSVファイル保存
        result_filename = self._get_result_filename(prompt_name)
        with open(path / result_filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(headers)
            writer.writerows(rows)

    def _validate_report_path(self, report_dir: str, prompt_name: str | None = None) -> Path:
        """レポートディレクトリのパスを検証する。

        Args:
            report_dir: レポートディレクトリパス。
            prompt_name: プロンプト名。

        Returns:
            Path: 検証済みのresult.tsvファイルパス。

        Raises:
            InvalidFilePathError: ファイルパスが不正な場合。
        """
        base_path = Path(self.base_dir).resolve()
        report_dir_path = Path(report_dir).resolve()
        result_filename = self._get_result_filename(prompt_name)
        result_path = (report_dir_path / result_filename).resolve()

        if not str(result_path).startswith(str(base_path)):
            raise InvalidFilePathError(report_dir)

        return result_path

    def _get_prompt_filename(self, prompt_name: str | None) -> str:
        """プロンプトファイル名を取得する。

        Args:
            prompt_name: プロンプト名。

        Returns:
            str: プロンプトファイル名。
        """
        if prompt_name:
            # プロンプト名から末尾の番号を抽出（例: prompt_1_1 -> _1_1）
            # プロンプト名が prompt_1_1 の場合、prompt_ を除いた部分を取得
            if prompt_name.startswith('prompt_'):
                suffix = prompt_name[len('prompt_') :]
                return f'prompt_{suffix}.md'
            # プロンプト名が prompt_ で始まらない場合も考慮
            return f'{prompt_name}.md'
        return 'prompt.txt'

    def _get_result_filename(self, prompt_name: str | None) -> str:
        """結果TSVファイル名を取得する。

        Args:
            prompt_name: プロンプト名。

        Returns:
            str: 結果TSVファイル名。
        """
        if prompt_name:
            # プロンプト名から末尾の番号を抽出（例: prompt_1_1 -> _1_1）
            # プロンプト名が prompt_1_1 の場合、prompt_ を除いた部分を取得
            if prompt_name.startswith('prompt_'):
                suffix = prompt_name[len('prompt_') :]
                return f'result_{suffix}.tsv'
            # プロンプト名が prompt_ で始まらない場合も考慮
            return f'result_{prompt_name}.tsv'
        return 'result.tsv'

    def _read_tsv_file(self, result_path: Path) -> tuple[list[str], list[list[str]]]:
        """TSVファイルを読み込む。

        Args:
            result_path: TSVファイルのパス。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。
        """
        if not result_path.exists():
            return [], []

        with open(result_path, encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
            if not rows:
                return [], []
            return rows[0], rows[1:]

    async def get_report_content(self, report_id: int) -> tuple[list[str], list[list[str]]]:
        """レポートの内容を取得する。

        Args:
            report_id: レポートID。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。

        Raises:
            ResourceNotFoundError: レポートが見つからない場合。
            ValueError: ファイルパスが不正な場合。
        """
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise ResourceNotFoundError(resource_name='Report', resource_id=str(report_id))

        result_path = self._validate_report_path(report.directory_path, report.prompt_name)
        return self._read_tsv_file(result_path)

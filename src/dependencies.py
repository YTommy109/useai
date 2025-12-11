"""依存性注入用の関数を定義するモジュール。

このモジュールは、FastAPIのDependsを使用してリポジトリとサービスを
依存性注入するための関数を提供します。
"""

from fastapi import BackgroundTasks, Depends
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.repositories import CountryRepository, RegulationRepository, ReportRepository
from src.services.country_service import CountryService
from src.services.export_service import ExportService
from src.services.llm_service import LLMService
from src.services.page_service import PageService
from src.services.prompt_service import PromptService
from src.services.regulation_service import RegulationService
from src.services.report_service import ReportService
from src.usecases import (
    CreateReportUseCase,
    DownloadReportUseCase,
    GetReportsUseCase,
    PreviewPromptUseCase,
)
from src.utils.template_utils import get_templates


def get_country_repository(
    session: AsyncSession = Depends(get_session),
) -> CountryRepository:
    """国リポジトリを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        CountryRepository: 国リポジトリインスタンス。
    """
    return CountryRepository(session)


def get_regulation_repository(
    session: AsyncSession = Depends(get_session),
) -> RegulationRepository:
    """規制リポジトリを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        RegulationRepository: 規制リポジトリインスタンス。
    """
    return RegulationRepository(session)


def get_report_repository(
    session: AsyncSession = Depends(get_session),
) -> ReportRepository:
    """レポートリポジトリを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        ReportRepository: レポートリポジトリインスタンス。
    """
    return ReportRepository(session)


def get_country_service(
    session: AsyncSession = Depends(get_session),
) -> CountryService:
    """国サービスを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        CountryService: 国サービスインスタンス。
    """
    return CountryService(CountryRepository(session), session)


def get_regulation_service(
    session: AsyncSession = Depends(get_session),
) -> RegulationService:
    """規制サービスを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        RegulationService: 規制サービスインスタンス。
    """
    return RegulationService(RegulationRepository(session), session)


def get_report_service(
    session: AsyncSession = Depends(get_session),
) -> ReportService:
    """レポートサービスを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        ReportService: レポートサービスインスタンス。
    """
    return ReportService(ReportRepository(session), session, LLMService())


def get_page_service(
    session: AsyncSession = Depends(get_session),
) -> PageService:
    """ページサービスを取得する。

    Args:
        session: 非同期データベースセッション。

    Returns:
        PageService: ページサービスインスタンス。
    """
    return PageService(
        CountryRepository(session),
        RegulationRepository(session),
        ReportRepository(session),
    )


class PageDependencies:
    """ページ表示に必要な依存性をまとめたクラス。"""

    def __init__(
        self,
        page_service: PageService,
        templates: Jinja2Templates,
    ) -> None:
        """初期化。

        Args:
            page_service: ページサービス。
            templates: Jinja2テンプレートインスタンス。
        """
        self.page_service = page_service
        self.templates = templates


def get_page_dependencies(
    page_service: PageService = Depends(get_page_service),
    templates: Jinja2Templates = Depends(get_templates),
) -> PageDependencies:
    """ページ表示に必要な依存性を取得する。

    Args:
        page_service: ページサービス。
        templates: Jinja2テンプレートインスタンス。

    Returns:
        PageDependencies: ページ表示に必要な依存性。
    """
    return PageDependencies(page_service, templates)


def get_export_service() -> ExportService:
    """エクスポートサービスを取得する。

    Returns:
        ExportService: エクスポートサービスインスタンス。
    """
    return ExportService()


def get_prompt_service() -> PromptService:
    """プロンプトサービスを取得する。

    Returns:
        PromptService: プロンプトサービスインスタンス。
    """
    return PromptService()


def get_create_report_usecase(
    background_tasks: BackgroundTasks,
    report_service: ReportService = Depends(get_report_service),
    report_repository: ReportRepository = Depends(get_report_repository),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> CreateReportUseCase:
    """レポート作成ユースケースを取得する。

    Args:
        background_tasks: バックグラウンドタスク。
        report_service: レポートサービス。
        report_repository: レポートリポジトリ。
        prompt_service: プロンプトサービス。

    Returns:
        CreateReportUseCase: レポート作成ユースケースインスタンス。
    """
    return CreateReportUseCase(report_service, report_repository, prompt_service, background_tasks)


def get_get_reports_usecase(
    report_repository: ReportRepository = Depends(get_report_repository),
) -> GetReportsUseCase:
    """レポート一覧取得ユースケースを取得する。

    Args:
        report_repository: レポートリポジトリ。

    Returns:
        GetReportsUseCase: レポート一覧取得ユースケースインスタンス。
    """
    return GetReportsUseCase(report_repository)


def get_preview_prompt_usecase(
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PreviewPromptUseCase:
    """プロンプトプレビューユースケースを取得する。

    Args:
        prompt_service: プロンプトサービス。

    Returns:
        PreviewPromptUseCase: プロンプトプレビューユースケースインスタンス。
    """
    return PreviewPromptUseCase(prompt_service)


def get_download_report_usecase(
    report_service: ReportService = Depends(get_report_service),
    export_service: ExportService = Depends(get_export_service),
) -> DownloadReportUseCase:
    """レポートダウンロードユースケースを取得する。

    Args:
        report_service: レポートサービス。
        export_service: エクスポートサービス。

    Returns:
        DownloadReportUseCase: レポートダウンロードユースケースインスタンス。
    """
    return DownloadReportUseCase(report_service, export_service)

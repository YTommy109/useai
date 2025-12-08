"""依存性注入用の関数を定義するモジュール。

このモジュールは、FastAPIのDependsを使用してリポジトリとサービスを
依存性注入するための関数を提供します。
"""

from datetime import datetime

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_session
from src.repositories import CountryRepository, RegulationRepository, ReportRepository
from src.services.country_service import CountryService
from src.services.llm_service import LLMService
from src.services.page_service import PageService
from src.services.regulation_service import RegulationService
from src.services.report_service import ReportService


def datetimeformat(value: datetime) -> str:
    """datetimeオブジェクトを読みやすい形式に変換する。

    Args:
        value: 変換するdatetimeオブジェクト。

    Returns:
        str: フォーマットされた日時文字列。
    """
    return value.strftime('%Y/%m/%d %H:%M:%S')


def get_templates() -> Jinja2Templates:
    """Jinja2テンプレートインスタンスを取得する。

    Returns:
        Jinja2Templates: テンプレートインスタンス。
    """
    templates = Jinja2Templates(directory='src/templates')
    templates.env.filters['datetimeformat'] = datetimeformat
    return templates


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

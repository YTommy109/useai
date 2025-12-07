"""ページ表示用のサービス。

このモジュールは、ページ表示に必要なデータを取得するためのサービスを提供します。
"""

from src.db.models import Report
from src.repositories import CountryRepository, RegulationRepository, ReportRepository


class PageService:
    """ページ表示に必要なデータを取得するサービス。"""

    def __init__(
        self,
        country_repo: CountryRepository,
        regulation_repo: RegulationRepository,
        report_repo: ReportRepository,
    ) -> None:
        """初期化。

        Args:
            country_repo: 国リポジトリ。
            regulation_repo: 規制リポジトリ。
            report_repo: レポートリポジトリ。
        """
        self.country_repo = country_repo
        self.regulation_repo = regulation_repo
        self.report_repo = report_repo

    async def get_main_page_data(
        self,
    ) -> tuple[dict[str, list[str]], list[str], list[Report]]:
        """メインページに必要なデータを取得する。

        Returns:
            tuple[dict[str, list[str]], list[str], list[Report]]:
                大陸別の国データ、規制リスト、レポートリストのタプル。
        """
        grouped_countries = await self.country_repo.get_grouped_by_continent()
        regulations = await self.regulation_repo.get_all_names()
        reports = await self.report_repo.get_all_desc()
        return grouped_countries, regulations, reports

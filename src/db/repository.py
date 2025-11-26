"""データベースアクセス用のリポジトリクラス。

このモジュールは、Country および Regulation エンティティの
データベースクエリをカプセル化するリポジトリクラスを提供します。
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country, Regulation


class CountryRepository:
    """Country エンティティのデータベース操作用リポジトリ。

    Attributes:
        session: クエリ実行用の非同期データベースセッション。
    """

    def __init__(self, session: AsyncSession) -> None:
        """データベースセッションでリポジトリを初期化する。

        Args:
            session: 非同期データベースセッション。
        """
        self.session = session

    async def get_all_names(self) -> list[str]:
        """データベースからすべての国名を取得する。

        Returns:
            国名のリスト。
        """
        result = await self.session.exec(select(Country))
        return [c.name for c in result.all()]

    async def get_grouped_by_continent(self) -> dict[str, list[str]]:
        """大陸別にグループ化された国名を取得する。

        Returns:
            大陸名をキー、国名のリストを値とする辞書。
        """
        result = await self.session.exec(select(Country))
        countries = result.all()

        grouped: dict[str, list[str]] = {}
        for country in countries:
            if country.continent not in grouped:
                grouped[country.continent] = []
            grouped[country.continent].append(country.name)

        return grouped


class RegulationRepository:
    """Regulation エンティティのデータベース操作用リポジトリ。

    Attributes:
        session: クエリ実行用の非同期データベースセッション。
    """

    def __init__(self, session: AsyncSession) -> None:
        """データベースセッションでリポジトリを初期化する。

        Args:
            session: 非同期データベースセッション。
        """
        self.session = session

    async def get_all_names(self) -> list[str]:
        """データベースからすべての規制名を取得する。

        Returns:
            規制名のリスト。
        """
        result = await self.session.exec(select(Regulation))
        return [r.name for r in result.all()]

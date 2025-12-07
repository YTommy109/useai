"""Country エンティティのデータベース操作用リポジトリ。

このモジュールは、Country エンティティに対する
データベース操作を提供するリポジトリクラスを定義します。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country
from src.repositories.base import BaseRepository


class CountryRepository(BaseRepository[Country]):
    """Country エンティティのデータベース操作用リポジトリ。

    Attributes:
        session: クエリ実行用の非同期データベースセッション。
    """

    def __init__(self, session: AsyncSession) -> None:
        """データベースセッションでリポジトリを初期化する。

        Args:
            session: 非同期データベースセッション。
        """
        super().__init__(session, Country)

    async def get_all_names(self) -> list[str]:
        """データベースからすべての国名を取得する。

        Returns:
            国名のリスト。
        """
        countries = await self.get_all()
        return [c.name for c in countries]

    async def get_grouped_by_continent(self) -> dict[str, list[str]]:
        """大陸別にグループ化された国名を取得する。

        Returns:
            大陸名をキー、国名のリストを値とする辞書。
        """
        countries = await self.get_all()

        grouped: dict[str, list[str]] = {}
        for country in countries:
            if country.continent not in grouped:
                grouped[country.continent] = []
            grouped[country.continent].append(country.name)

        return grouped

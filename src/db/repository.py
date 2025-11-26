"""データベースアクセス用のリポジトリクラス。

このモジュールは、Country および Regulation エンティティの
データベースクエリをカプセル化するリポジトリクラスを提供します。
"""

from sqlmodel import SQLModel, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country, Regulation


class BaseRepository[ModelType: SQLModel]:
    """データベース操作の基底リポジトリクラス。

    Attributes:
        session: クエリ実行用の非同期データベースセッション。
        model: 操作対象のモデルクラス。
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        """データベースセッションとモデルでリポジトリを初期化する。

        Args:
            session: 非同期データベースセッション。
            model: 操作対象のモデルクラス。
        """
        self.session = session
        self.model = model

    async def count(self) -> int:
        """データベース内のレコード総数を取得する。

        Returns:
            レコードの総数。
        """
        result = await self.session.exec(select(func.count()).select_from(self.model))
        return result.one()

    async def delete_all(self) -> None:
        """データベースからすべてのレコードを削除する。"""
        await self.session.exec(delete(self.model))
        await self.session.commit()

    async def get_all(self) -> list[ModelType]:
        """データベースからすべてのレコードを取得する。

        Returns:
            モデルインスタンスのリスト。
        """
        result = await self.session.exec(select(self.model))
        return list(result.all())


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


class RegulationRepository(BaseRepository[Regulation]):
    """Regulation エンティティのデータベース操作用リポジトリ。

    Attributes:
        session: クエリ実行用の非同期データベースセッション。
    """

    def __init__(self, session: AsyncSession) -> None:
        """データベースセッションでリポジトリを初期化する。

        Args:
            session: 非同期データベースセッション。
        """
        super().__init__(session, Regulation)

    async def get_all_names(self) -> list[str]:
        """データベースからすべての規制名を取得する。

        Returns:
            規制名のリスト。
        """
        regulations = await self.get_all()
        return [r.name for r in regulations]

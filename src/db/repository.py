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

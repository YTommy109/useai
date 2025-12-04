"""データベースアクセス用のリポジトリクラス。

このモジュールは、Country および Regulation エンティティの
データベースクエリをカプセル化するリポジトリクラスを提供します。
"""

from sqlmodel import SQLModel, col, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country, Regulation, Report


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

    async def get_all(self) -> list[ModelType]:
        """データベースからすべてのレコードを取得する。

        Returns:
            モデルインスタンスのリスト。
        """
        result = await self.session.exec(select(self.model))
        return list(result.all())

    async def get_by_id(self, record_id: int) -> ModelType | None:
        """IDでレコードを取得する。

        Args:
            record_id: レコードID。

        Returns:
            ModelType | None: 取得したレコード。存在しない場合は None。
        """
        return await self.session.get(self.model, record_id)

    async def create(self, instance: ModelType) -> ModelType:
        """レコードを作成する。

        Args:
            instance: 作成するモデルインスタンス。

        Returns:
            ModelType: 作成されたモデルインスタンス。
        """
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """レコードを更新する。

        Args:
            instance: 更新するモデルインスタンス。

        Returns:
            ModelType: 更新されたモデルインスタンス。
        """
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance


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
    """規制リポジトリ。"""

    def __init__(self, session: AsyncSession) -> None:
        """初期化。

        Args:
            session: 非同期データベースセッション。
        """
        super().__init__(session, Regulation)

    async def get_all_names(self) -> list[str]:
        """すべての規制名を取得する。

        Returns:
            list[str]: 規制名のリスト。
        """
        statement = select(self.model.name)
        result = await self.session.exec(statement)
        return list(result.all())


class ReportRepository(BaseRepository[Report]):
    """レポートリポジトリ。"""

    def __init__(self, session: AsyncSession) -> None:
        """初期化。

        Args:
            session: 非同期データベースセッション。
        """
        super().__init__(session, Report)

    async def get_all_desc(self) -> list[Report]:
        """すべてのレポートを作成日時の降順で取得する。

        Returns:
            list[Report]: レポートのリスト。
        """
        statement = select(self.model).order_by(col(self.model.created_at).desc())
        result = await self.session.exec(statement)
        return list(result.all())

"""データベース操作の基底リポジトリクラス。

このモジュールは、すべてのリポジトリクラスの基底となる
BaseRepository クラスを提供します。
"""

from sqlmodel import SQLModel, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession


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

    async def delete_all(self) -> int:
        """データベースからすべてのレコードを削除する。

        Returns:
            int: 削除されたレコード数。
        """
        # 削除前に件数を取得
        count_before = await self.count()
        await self.session.exec(delete(self.model))
        return count_before

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

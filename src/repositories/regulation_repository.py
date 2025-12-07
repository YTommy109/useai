"""Regulation エンティティのデータベース操作用リポジトリ。

このモジュールは、Regulation エンティティに対する
データベース操作を提供するリポジトリクラスを定義します。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Regulation
from src.repositories.base import BaseRepository


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
        regulations = await self.get_all()
        return [r.name for r in regulations]

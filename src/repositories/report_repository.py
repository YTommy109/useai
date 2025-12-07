"""Report エンティティのデータベース操作用リポジトリ。

このモジュールは、Report エンティティに対する
データベース操作を提供するリポジトリクラスを定義します。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Report
from src.repositories.base import BaseRepository


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
        reports = await self.get_all()
        return sorted(reports, key=lambda r: r.created_at, reverse=True)

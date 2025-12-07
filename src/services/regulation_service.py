"""規制データに関するビジネスロジックを提供するサービスモジュール。"""

import csv
from pathlib import Path

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Regulation
from src.exceptions import ResourceNotFoundError
from src.repositories import RegulationRepository


class RegulationService:
    """規制データに関するビジネスロジックを提供するサービス。

    Attributes:
        repository: 規制データのリポジトリ。
        session: データベースセッション。
    """

    def __init__(self, repository: RegulationRepository, session: AsyncSession) -> None:
        """サービスを初期化する。

        Args:
            repository: 規制データのリポジトリ。
            session: データベースセッション。
        """
        self.repository = repository
        self.session = session

    async def import_from_csv(self, csv_path: Path) -> int:
        """CSV ファイルから規制データをインポートする。

        既存のデータはすべて削除され、CSV の内容で置き換えられます。

        Args:
            csv_path: CSV ファイルのパス。

        Returns:
            インポートされたレコード数。

        Raises:
            ResourceNotFoundError: CSV ファイルが存在しない場合。
        """
        if not csv_path.exists():
            raise ResourceNotFoundError(resource_name='CSV file', resource_id=str(csv_path))

        # 既存データを削除
        await self.repository.delete_all()

        # CSV ファイルを読み込んで追加
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.session.add(Regulation(name=row['name']))

        # トランザクションをコミット
        await self.session.commit()

        # 件数を返す
        return await self.repository.count()

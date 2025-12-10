"""アプリケーションのデータベースモデル。

このモジュールは、データベーステーブルを表す SQLModel クラスを定義します。
"""

from datetime import UTC, datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class Country(SQLModel, table=True):
    """国エンティティを表す Country モデル。

    Attributes:
        id: 主キー識別子。
        name: 国名。
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str
    continent: str


class Regulation(SQLModel, table=True):
    """規制エンティティを表す Regulation モデル。

    Attributes:
        id: 主キー識別子。
        name: 規制名。
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str


class ReportStatus(StrEnum):
    """レポートのステータス。"""

    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class Report(SQLModel, table=True):
    """レポートエンティティを表す Report モデル。

    Attributes:
        id: 主キー識別子。
        created_at: 作成日時（UTC）。
        status: ステータス（processing, completed, failed）。
        directory_path: 保存先ディレクトリパス。
        prompt_name: 使用したプロンプト名。
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    status: ReportStatus
    directory_path: str
    prompt_name: str | None = Field(default=None)

    @property
    def created_at_jst(self) -> datetime:
        """作成日時をJST（日本標準時）で取得する。

        Returns:
            datetime: JSTに変換された作成日時。
        """
        # SQLiteにはタイムゾーン情報がないため、UTCとして扱う
        if self.created_at.tzinfo is None:
            # タイムゾーン情報がない場合はUTCとして扱う
            utc_dt = self.created_at.replace(tzinfo=UTC)
        else:
            utc_dt = self.created_at.astimezone(UTC)

        # JST（Asia/Tokyo）に変換
        return utc_dt.astimezone(ZoneInfo('Asia/Tokyo'))

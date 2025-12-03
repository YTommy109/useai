"""アプリケーションのデータベースモデル。

このモジュールは、データベーステーブルを表す SQLModel クラスを定義します。
"""

from datetime import datetime
from enum import StrEnum

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
        created_at: 作成日時。
        status: ステータス（processing, completed, failed）。
        directory_path: 保存先ディレクトリパス。
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    status: ReportStatus
    directory_path: str

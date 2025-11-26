"""アプリケーションのデータベースモデル。

このモジュールは、データベーステーブルを表す SQLModel クラスを定義します。
"""

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

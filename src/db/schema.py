"""データベーススキーマ DDL 生成ユーティリティ。

このモジュールは、データベーススキーマの DDL 文を生成して
出力するユーティリティを提供します。
"""

from typing import Any

from sqlalchemy import create_mock_engine
from sqlmodel import SQLModel


def dump_ddl(url: str) -> None:
    """データベーススキーマの DDL 文を生成して出力する。

    Args:
        url: データベース URL 文字列 (例: 'sqlite://')。
    """

    def dump(sql: Any, *multiparams: Any, **params: Any) -> None:
        print(
            str(sql.compile(dialect=engine.dialect)).replace('\t', '').replace('\n', ''), end=';\n'
        )

    engine = create_mock_engine(url, dump)
    SQLModel.metadata.create_all(engine, checkfirst=False)


if __name__ == '__main__':
    dump_ddl('sqlite://')

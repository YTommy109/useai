"""Jinja2テンプレートフィルター。

このモジュールは、Jinja2テンプレートで使用するカスタムフィルターを提供します。
"""

from datetime import datetime


def datetimeformat(value: datetime) -> str:
    """datetimeオブジェクトを読みやすい形式に変換する。

    Args:
        value: 変換するdatetimeオブジェクト。

    Returns:
        str: フォーマットされた日時文字列。
    """
    return value.strftime('%Y/%m/%d %H:%M:%S')

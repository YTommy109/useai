"""テンプレートユーティリティ。

このモジュールは、Jinja2テンプレートの設定と初期化を担当します。
"""

from fastapi.templating import Jinja2Templates

from src.utils.jinja2_filters import datetimeformat


def get_templates() -> Jinja2Templates:
    """Jinja2テンプレートインスタンスを取得する。

    Returns:
        Jinja2Templates: テンプレートインスタンス。
    """
    templates = Jinja2Templates(directory='src/templates')
    templates.env.filters['datetimeformat'] = datetimeformat
    return templates

"""アプリケーション設定モジュール。

このモジュールは、環境変数から設定を読み込むための
pydantic-settingsベースの設定クラスを提供します。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定。

    環境変数から設定を読み込み、デフォルト値を提供します。

    Attributes:
        database_url: データベース接続URL。
        sql_echo: SQLクエリをログに出力するかどうか。
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # データベース設定
    database_url: str = 'sqlite+aiosqlite:///./data/app.db'
    sql_echo: bool = False

    # ロギング設定
    log_level: str = 'INFO'

    # レポート設定
    report_base_dir: str = 'data/reports'
    report_preview_limit: int = 100

    # OpenAI設定
    openai_api_key: str = ''
    openai_api_base: str | None = None
    openai_model: str = 'gpt-4o-mini'


# グローバル設定インスタンス
settings = Settings()

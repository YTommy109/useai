"""ロギング設定モジュール。"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import settings

# アプリケーション用ロガー
logger = logging.getLogger('useai')


class JSONFormatter(logging.Formatter):
    """JSON Lines 形式のフォーマッタ。"""

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式の文字列に変換する。"""
        # タイムゾーン情報を付与してISOフォーマットに変換
        dt = datetime.fromtimestamp(record.created).astimezone()

        data: dict[str, Any] = {
            'timestamp': dt.isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'location': {
                'file': record.filename,
                'line': record.lineno,
                'module': record.module,
                'func': record.funcName,
            },
        }

        if record.exc_info:
            data['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(data, ensure_ascii=False)


def _setup_file_handler(log_file: Path) -> logging.Handler:
    """ファイルハンドラを作成する。"""
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=28,
        encoding='utf-8',
    )
    handler.setFormatter(JSONFormatter())
    return handler


def _setup_console_handler() -> logging.Handler:
    """コンソールハンドラを作成する。"""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    return handler


def _configure_library_loggers() -> None:
    """ライブラリのログ設定を調整する。"""
    # Uvicornのログをルートロガーに委譲
    for logger_name in ('uvicorn', 'uvicorn.access', 'uvicorn.error'):
        lib_logger = logging.getLogger(logger_name)
        lib_logger.handlers = []
        lib_logger.propagate = True

    # SQLAlchemyのログ設定
    sa_logger = logging.getLogger('sqlalchemy.engine')
    if settings.sql_echo:
        sa_logger.setLevel(logging.INFO)
    else:
        sa_logger.setLevel(logging.WARNING)


def init_logger() -> None:
    """ロガーを初期化する。

    ルートロガーに対して以下の設定を行う:
    1. ログレベルの設定 (環境変数から)
    2. ファイルハンドラ (JSONL形式, 日次ローテーション, 28日保存)
    3. コンソールハンドラ (標準フォーマット)
    """
    # ログディレクトリの作成
    log_dir = Path('.log')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'app.log'

    # ルートロガーの設定
    root_logger = logging.getLogger()
    log_level = settings.log_level.upper()
    root_logger.setLevel(log_level)

    # 既存のハンドラをクリア（二重登録防止）
    root_logger.handlers.clear()

    # ハンドラの追加
    root_logger.addHandler(_setup_file_handler(log_file))
    root_logger.addHandler(_setup_console_handler())

    # ライブラリ設定
    _configure_library_loggers()

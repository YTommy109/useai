"""ロギング設定モジュール。"""

import logging
import sys

# ロガーの初期化
logger = logging.getLogger('useai')


def init_logger() -> None:
    """ロガーを初期化する。"""
    logger.setLevel(logging.INFO)

    # コンソールハンドラ
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

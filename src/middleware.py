"""ロギングミドルウェアモジュール。"""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """全てのリクエストとレスポンスをログ出力するミドルウェア。"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """リクエストを処理し、ログを出力する。

        Args:
            request: 受信したリクエスト
            call_next: 次のミドルウェアまたはルートハンドラ

        Returns:
            Response: 生成されたレスポンス
        """
        start_time = time.perf_counter()

        # リクエストログ（メソッド、パス、クライアント）
        # clientがNoneの場合を考慮
        client = f'{request.client.host}:{request.client.port}' if request.client else 'unknown'
        logger.info(f'Request: {request.method} {request.url.path} from {client}')

        try:
            response = await call_next(request)

            # 処理時間計測
            process_time = time.perf_counter() - start_time

            # レスポンスログ
            logger.info(f'Response: {response.status_code} processed in {process_time:.3f}s')

            return response

        except Exception as e:
            # 予期せぬエラーのログ出力（スタックトレース含む）
            process_time = time.perf_counter() - start_time
            logger.error(
                f'Request failed: {type(e).__name__}: {e!s} after {process_time:.3f}s',
                exc_info=True,
            )
            raise  # FastAPIのデフォルト例外ハンドラに任せる（500エラー返却）

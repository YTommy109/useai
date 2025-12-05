"""ロギングミドルウェアモジュール。"""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.exceptions import AppError, ResourceNotFoundError
from src.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """全てのリクエストとレスポンスをログ出力するミドルウェア。"""

    async def dispatch(  # noqa: PLR0915
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """リクエストを処理する。

        Args:
            request: リクエストオブジェクト。
            call_next: 次の処理を呼び出す関数。

        Returns:
            Response: レスポンスオブジェクト。
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

        except ResourceNotFoundError as e:
            # リソースが見つからない場合は404を返す
            process_time = time.perf_counter() - start_time
            logger.warning(f'Resource not found: {e!s} after {process_time:.3f}s')
            return JSONResponse(status_code=404, content={'message': str(e)})

        except AppError as e:
            # アプリケーション固有の例外は400エラー系として扱う
            process_time = time.perf_counter() - start_time
            logger.warning(f'Application error: {e!s} after {process_time:.3f}s')
            return JSONResponse(status_code=400, content={'message': str(e)})

        except Exception as e:
            # 予期せぬエラーのログ出力（スタックトレース含む）
            process_time = time.perf_counter() - start_time
            logger.error(
                f'Request failed: {type(e).__name__}: {e!s} after {process_time:.3f}s',
                exc_info=True,
            )
            raise  # FastAPIのデフォルト例外ハンドラに任せる（500エラー返却）

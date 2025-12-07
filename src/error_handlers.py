"""グローバルエラーハンドラー。

このモジュールは、アプリケーション全体のエラーハンドリングを統一します。
"""

from fastapi import Request, status
from fastapi.responses import HTMLResponse, JSONResponse

from src.exceptions import (
    BusinessError,
    InvalidFilePathError,
    ResourceNotFoundError,
    ValidationError,
)
from src.logger import logger


async def resource_not_found_handler(
    request: Request, exc: ResourceNotFoundError
) -> HTMLResponse | JSONResponse:
    """リソースが見つからない例外のハンドラー。

    Args:
        request: FastAPIリクエストオブジェクト。
        exc: ResourceNotFoundError例外。

    Returns:
        HTMLResponse | JSONResponse: 404エラーレスポンス。
    """
    logger.warning(f'Resource not found: {exc}')

    # HTMX リクエストの場合はHTMLを返す
    if request.headers.get('HX-Request'):
        return HTMLResponse(
            content=f'<div style="color: red;">{exc}</div>',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'error': str(exc)},
    )


async def invalid_file_path_handler(
    request: Request, exc: InvalidFilePathError
) -> HTMLResponse | JSONResponse:
    """不正なファイルパス例外のハンドラー。

    Args:
        request: FastAPIリクエストオブジェクト。
        exc: InvalidFilePathError例外。

    Returns:
        HTMLResponse | JSONResponse: 400エラーレスポンス。
    """
    logger.error(f'Invalid file path detected: {exc.file_path}', exc_info=True)

    # セキュリティ上の理由で詳細は返さない
    error_message = 'ファイルパスが不正です'

    if request.headers.get('HX-Request'):
        return HTMLResponse(
            content=f'<div style="color: red;">{error_message}</div>',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'error': error_message},
    )


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> HTMLResponse | JSONResponse:
    """バリデーションエラーのハンドラー。

    Args:
        request: FastAPIリクエストオブジェクト。
        exc: ValidationError例外。

    Returns:
        HTMLResponse | JSONResponse: 422エラーレスポンス。
    """
    logger.warning(f'Validation error: {exc}')

    if request.headers.get('HX-Request'):
        return HTMLResponse(
            content=f'<div style="color: red;">入力エラー: {exc}</div>',
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'error': str(exc)},
    )


async def business_error_handler(
    request: Request, exc: BusinessError
) -> HTMLResponse | JSONResponse:
    """ビジネスエラーのハンドラー。

    Args:
        request: FastAPIリクエストオブジェクト。
        exc: BusinessError例外。

    Returns:
        HTMLResponse | JSONResponse: 400エラーレスポンス。
    """
    logger.warning(f'Business error: {exc}')

    if request.headers.get('HX-Request'):
        return HTMLResponse(
            content=f'<div style="color: red;">{exc}</div>',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'error': str(exc)},
    )

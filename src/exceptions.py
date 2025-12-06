"""アプリケーション固有の例外クラス定義モジュール。

標準の例外の代わりにこれらを使用することで、
エラーハンドリングの一貫性を保ちます。
"""


class AppError(Exception):
    """アプリケーションの基底例外クラス。"""

    def __init__(self, message: str) -> None:
        """初期化。

        Args:
           message: エラーメッセージ
        """
        super().__init__(message)


class ResourceNotFoundError(AppError):
    """リソースが見つからない場合に発生する例外。

    Args:
        resource_name: リソース名（例: "Report", "CSV file"）
        resource_id: リソースのIDやパス（オプション）
    """

    def __init__(self, resource_name: str, resource_id: str | None = None) -> None:
        """初期化。

        Args:
            resource_name: リソース名
            resource_id: リソースID (Optional)
        """
        if resource_id:
            message = f'{resource_name} not found: {resource_id}'
        else:
            message = f'{resource_name} not found'
        super().__init__(message)


class BusinessError(AppError):
    """ビジネスルールに違反した場合に発生する例外。

    例:
        - 許可されていない操作
        - データの不整合
    """


class InvalidFilePathError(AppError):
    """ファイルパスが不正な場合に発生する例外。

    例:
        - パストラバーサル攻撃の試み
        - 不正なファイルパス
    """

    def __init__(self, file_path: str) -> None:
        """初期化。

        Args:
            file_path: 不正なファイルパス。
        """
        super().__init__(f'Invalid file path: {file_path}')
        self.file_path = file_path


class ValidationError(AppError):
    """入力検証エラー。

    例:
        - 必須フィールドの欠落
        - 不正な形式のデータ
    """

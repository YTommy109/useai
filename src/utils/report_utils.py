"""レポート生成関連のユーティリティ関数。

このモジュールは、レポート生成に関連する純粋関数を提供します。
"""

from pathlib import Path

from src.exceptions import ResourceNotFoundError


class PromptGenerator:
    """プロンプトテキストを生成するクラス。

    テンプレートファイルの読み込みとプレースホルダーの置換を担当します。
    """

    # テンプレートファイルのパス（プロジェクトルートからの相対パス）
    # __file__からプロジェクトルートを計算
    _current_file = Path(__file__)
    _project_root = _current_file.parent.parent.parent
    template_path: Path = _project_root / 'data' / 'prompt' / 'prompt_1_1.md'

    def get_name(self) -> str:
        """プロンプト名を取得する。

        Returns:
            str: プロンプト名（拡張子なし）。
        """
        return self.template_path.stem

    def load_template(self) -> str:
        """テンプレートファイルを読み込む。

        Returns:
            str: テンプレートファイルの内容。

        Raises:
            ResourceNotFoundError: テンプレートファイルが見つからない場合。
        """
        if not self.template_path.exists():
            raise ResourceNotFoundError('Prompt template file', str(self.template_path))

        return self.template_path.read_text(encoding='utf-8')

    def generate(self, countries: list[str], regulations: list[str]) -> str:
        """プロンプトテキストを生成する。

        Args:
            countries: 選択された国名のリスト。
            regulations: 選択された規制名のリスト。

        Returns:
            str: 生成されたプロンプトテキスト。

        Raises:
            ResourceNotFoundError: テンプレートファイルが見つからない場合。
        """
        template_content = self.load_template()

        # 国と法規を改行区切りの文字列に変換
        country_text = '\n'.join(countries) if countries else ''
        regulation_text = '\n'.join(regulations) if regulations else ''

        # プレースホルダーを置換
        return template_content.replace('${COUNTRY}', country_text).replace(
            '${REGULATION}', regulation_text
        )

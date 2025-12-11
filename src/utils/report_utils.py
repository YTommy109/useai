"""レポート生成関連のユーティリティ関数。

このモジュールは、レポート生成に関連する純粋関数を提供します。
"""

import csv
import io
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
    _prompt_dir: Path = _project_root / 'data' / 'prompt'

    def get_all_prompt_files(self) -> list[Path]:
        """data/promptディレクトリ内のプロンプトファイルをファイル名の昇順で取得する。

        Returns:
            list[Path]: プロンプトファイルのパスのリスト（ファイル名の昇順）。
        """
        if not self._prompt_dir.exists():
            raise ResourceNotFoundError('Prompt directory', str(self._prompt_dir))

        # .mdファイルをファイル名の昇順で取得
        return sorted(self._prompt_dir.glob('*.md'))

    def get_name(self) -> str:
        """最初のプロンプト名を取得する。

        Returns:
            str: プロンプト名（拡張子なし）。
        """
        prompt_files = self.get_all_prompt_files()
        if not prompt_files:
            raise ResourceNotFoundError('Prompt template file', str(self._prompt_dir))
        return prompt_files[0].stem

    def load_template(self, template_path: Path) -> str:
        """テンプレートファイルを読み込む。

        Args:
            template_path: テンプレートファイルのパス。

        Returns:
            str: テンプレートファイルの内容。

        Raises:
            ResourceNotFoundError: テンプレートファイルが見つからない場合。
        """
        if not template_path.exists():
            raise ResourceNotFoundError('Prompt template file', str(template_path))

        return template_path.read_text(encoding='utf-8')

    def generate_first_prompt(self, countries: list[str], regulations: list[str]) -> str:
        """最初のプロンプトテキストを生成する。

        Args:
            countries: 選択された国名のリスト。
            regulations: 選択された規制名のリスト。

        Returns:
            str: 生成されたプロンプトテキスト。

        Raises:
            ResourceNotFoundError: テンプレートファイルが見つからない場合。
        """
        prompt_files = self.get_all_prompt_files()
        if not prompt_files:
            raise ResourceNotFoundError('Prompt template file', str(self._prompt_dir))

        template_content = self.load_template(prompt_files[0])

        # 国と法規を改行区切りの文字列に変換
        country_text = '\n'.join(countries) if countries else ''
        regulation_text = '\n'.join(regulations) if regulations else ''

        # プレースホルダーを置換
        return template_content.replace('${COUNTRY}', country_text).replace(
            '${REGULATION}', regulation_text
        )

    def generate_next_prompt(self, template_path: Path, previous_result: str) -> str:
        """次のプロンプトテキストを生成する（前の結果を埋め込む）。

        Args:
            template_path: テンプレートファイルのパス。
            previous_result: 前のプロンプトの実行結果（TSV形式の文字列）。

        Returns:
            str: 生成されたプロンプトテキスト。

        Raises:
            ResourceNotFoundError: テンプレートファイルが見つからない場合。
        """
        template_content = self.load_template(template_path)

        # 前の結果を埋め込む
        return template_content.replace('${PREVIOUS_RESULT}', previous_result)

    @staticmethod
    def format_tsv_result(headers: list[str], rows: list[list[str]]) -> str:
        """TSV結果を文字列形式に変換する。

        Args:
            headers: ヘッダー行。
            rows: データ行のリスト。

        Returns:
            str: TSV形式の文字列。
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()

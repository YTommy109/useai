"""レポート生成関連のユーティリティ関数。

このモジュールは、レポート生成に関連する純粋関数を提供します。
"""

import random
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


def generate_dummy_data() -> tuple[list[str], list[list[str]]]:
    """ダミーデータを生成する。

    Returns:
        tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。
    """
    headers = [f'項目{i + 1}' for i in range(20)]
    rows = []
    for i in range(50):
        row = [f'データ{i + 1}-{j + 1}' for j in range(20)]
        # それっぽいデータを入れる
        row[2] = random.choice(['適合', '要確認', '不適合', '保留'])  # noqa: S311
        row[5] = random.choice(['あり', 'なし', '不明'])  # noqa: S311
        row[8] = str(random.randint(1, 100))  # noqa: S311
        row[12] = random.choice(['A', 'B', 'C', 'D', 'E'])  # noqa: S311
        rows.append(row)
    return headers, rows

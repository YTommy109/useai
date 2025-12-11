"""プロンプトサービスモジュール。

このモジュールは、プロンプトテキストの生成機能を提供します。
"""

from pathlib import Path

from src.exceptions import ResourceNotFoundError


class PromptService:
    """プロンプトサービス。

    テンプレートファイルの読み込みとプレースホルダーの置換を担当します。
    """

    def __init__(self, prompt_dir: Path | None = None) -> None:
        """初期化。

        Args:
            prompt_dir: プロンプトファイルのディレクトリパス。
                Noneの場合はデフォルトのパスを使用。
        """
        if prompt_dir is None:
            _current_file = Path(__file__)
            _project_root = _current_file.parent.parent.parent
            self.prompt_dir = _project_root / 'data' / 'prompt'
        else:
            self.prompt_dir = prompt_dir

    def get_prompt_name(self) -> str:
        """プロンプト名を取得する。

        Returns:
            str: プロンプト名（拡張子なし）。

        Raises:
            ResourceNotFoundError: プロンプトファイルが見つからない場合。
        """
        prompt_files = self._get_prompt_files()
        if not prompt_files:
            raise ResourceNotFoundError('Prompt template file', str(self.prompt_dir))
        return prompt_files[0].stem

    def _get_prompt_files(self) -> list[Path]:
        """プロンプトファイルのリストを取得する。

        Returns:
            list[Path]: プロンプトファイルのパスリスト（昇順ソート）。
        """
        if not self.prompt_dir.exists():
            raise ResourceNotFoundError('Prompt directory', str(self.prompt_dir))
        return sorted(self.prompt_dir.glob('*.md'))

    def load_template(self, template_path: Path | None = None) -> str:
        """テンプレートファイルを読み込む。

        Args:
            template_path: テンプレートファイルのパス。
                Noneの場合は最初のプロンプトファイルを使用。

        Returns:
            str: テンプレートファイルの内容。

        Raises:
            ResourceNotFoundError: テンプレートファイルが見つからない場合。
        """
        if template_path is None:
            prompt_files = self._get_prompt_files()
            if not prompt_files:
                raise ResourceNotFoundError('Prompt template file', str(self.prompt_dir))
            template_path = prompt_files[0]

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
        template_content = self.load_template()

        # 国と法規を改行区切りの文字列に変換
        country_text = '\n'.join(countries) if countries else ''
        regulation_text = '\n'.join(regulations) if regulations else ''

        # プレースホルダーを置換
        return template_content.replace('${COUNTRY}', country_text).replace(
            '${REGULATION}', regulation_text
        )

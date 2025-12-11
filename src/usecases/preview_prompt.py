"""プロンプトプレビューユースケース。"""

import markdown

from src.services.prompt_service import PromptService


class PreviewPromptUseCase:
    """プロンプトプレビューユースケース。"""

    def __init__(self, prompt_service: PromptService) -> None:
        """初期化。

        Args:
            prompt_service: プロンプトサービス。
        """
        self.prompt_service = prompt_service

    async def execute(
        self, countries: list[str], regulations: list[str]
    ) -> tuple[str, list[str], list[str]]:
        """プロンプトのプレビューを生成する。

        Args:
            countries: 選択された国名のリスト。
            regulations: 選択された規制名のリスト。

        Returns:
            tuple[str, list[str], list[str]]: プロンプトHTML、選択された国名リスト、
                選択された規制名リスト。
        """
        prompt = self.prompt_service.generate_first_prompt(countries, regulations)
        prompt_html = markdown.markdown(prompt)
        return prompt_html, countries, regulations

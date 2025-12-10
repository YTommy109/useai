"""LLMサービスモジュール。

このモジュールは、OpenAI APIを使用してLLMに問い合わせる機能を提供します。
"""

import csv
import io
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from src.config import settings

if TYPE_CHECKING:
    pass


class LLMService:
    """LLMサービス。

    OpenAI APIを使用してLLMに問い合わせます。
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """初期化。

        Args:
            api_key: OpenAI API KEY。Noneの場合は設定から取得。
            model: OpenAIモデル名。Noneの場合は設定から取得。
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        if settings.openai_api_base:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=settings.openai_api_base)
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_tsv(self, prompt: str) -> tuple[list[str], list[list[str]]]:
        """プロンプトを使用してLLMからTSVデータを生成する。

        Args:
            prompt: プロンプトテキスト。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。

        Raises:
            ValueError: LLMのレスポンスがTSV形式でない場合。
        """
        # TSV形式で返すように指示を追加
        system_prompt = (
            'あなたはTSV（タブ区切り値）形式のデータを生成するアシスタントです。'
            'プロンプトの指示に従って、TSV形式のデータを生成してください。'
            'レスポンスは、1行目がヘッダー行（タブ区切り）、2行目以降がデータ行（タブ区切り）となる形式で返してください。'
            'コードブロックやマークダウン記法は使用せず、プレーンテキストのTSV形式のみを返してください。'
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError('LLM response is empty')

        # TSV形式のデータをパース
        return self._parse_tsv_response(content)

    def _parse_tsv_response(self, content: str) -> tuple[list[str], list[list[str]]]:
        """LLMのレスポンスをTSV形式にパースする。

        Args:
            content: LLMのレスポンステキスト。

        Returns:
            tuple[list[str], list[list[str]]]: ヘッダーと行データのタプル。

        Raises:
            ValueError: パースに失敗した場合。
        """
        # コードブロックやマークダウン記法を除去
        content = content.strip()
        if content.startswith('```'):
            # コードブロックを除去
            lines = content.split('\n')
            # 最初の```行と最後の```行を除去
            min_lines_for_code_block = 2
            if len(lines) > min_lines_for_code_block and lines[-1].strip() == '```':
                content = '\n'.join(lines[1:-1])
            elif len(lines) > 1:
                content = '\n'.join(lines[1:])

        # TSV形式でパース
        reader = csv.reader(io.StringIO(content), delimiter='\t')
        rows = list(reader)

        if not rows:
            raise ValueError('LLM response contains no data')

        headers = rows[0]
        data_rows = rows[1:]

        return headers, data_rows

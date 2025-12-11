"""prompt_service の単体テスト。"""

from pathlib import Path

import pytest

from src.exceptions import ResourceNotFoundError
from src.services.prompt_service import PromptService


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """プロンプトディレクトリのパスを返すフィクスチャ。"""
    return tmp_path / 'prompt'


@pytest.fixture
def prompt_service(prompt_dir: Path) -> PromptService:
    """PromptServiceインスタンスを返すフィクスチャ。"""
    return PromptService(prompt_dir=prompt_dir)


@pytest.mark.asyncio
async def test_テンプレートファイルの読み込みが成功する(
    prompt_service: PromptService, prompt_dir: Path
) -> None:
    # Arrange
    template_path = prompt_dir / 'template.md'
    prompt_dir.mkdir(parents=True, exist_ok=True)
    template_content = 'Template content'
    template_path.write_text(template_content, encoding='utf-8')

    # Act
    result = prompt_service.load_template(template_path)

    # Assert
    assert result == template_content


@pytest.mark.asyncio
async def test_テンプレートファイルが存在しない場合にResourceNotFoundErrorを発生させる(
    prompt_service: PromptService, prompt_dir: Path
) -> None:
    # Arrange
    prompt_dir.mkdir(parents=True, exist_ok=True)
    template_path = prompt_dir / 'nonexistent.md'

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Prompt template file'):
        prompt_service.load_template(template_path)


@pytest.mark.asyncio
async def test_プロンプト名を取得できる(prompt_service: PromptService, prompt_dir: Path) -> None:
    # Arrange
    prompt_dir.mkdir(parents=True, exist_ok=True)
    template_path = prompt_dir / 'prompt_1_1.md'
    template_path.write_text('Template content', encoding='utf-8')

    # Act
    result = prompt_service.get_prompt_name()

    # Assert
    assert result == 'prompt_1_1'


@pytest.mark.asyncio
async def test_プロンプトファイルが存在しない場合にResourceNotFoundErrorを発生させる(
    prompt_service: PromptService, prompt_dir: Path
) -> None:
    # Arrange
    prompt_dir.mkdir(parents=True, exist_ok=True)
    # プロンプトファイルは存在しない

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Prompt template file'):
        prompt_service.get_prompt_name()


@pytest.mark.parametrize(
    ('countries', 'regulations', 'expected'),
    [
        (
            ['Japan', 'USA'],
            ['GDPR', 'CCPA'],
            'Countries:\nJapan\nUSA\n\nRegulations:\nGDPR\nCCPA',
        ),
        ([], [], 'Countries:\n\n\nRegulations:\n'),
        (['Japan', 'USA'], [], 'Countries:\nJapan\nUSA\n\nRegulations:\n'),
        ([], ['GDPR', 'CCPA'], 'Countries:\n\n\nRegulations:\nGDPR\nCCPA'),
    ],
)
@pytest.mark.asyncio
async def test_プロンプト生成が成功する(
    prompt_service: PromptService,
    prompt_dir: Path,
    countries: list[str],
    regulations: list[str],
    expected: str,
) -> None:
    # Arrange
    prompt_dir.mkdir(parents=True, exist_ok=True)
    template_path = prompt_dir / 'prompt_1_1.md'
    template_content = 'Countries:\n${COUNTRY}\n\nRegulations:\n${REGULATION}'
    template_path.write_text(template_content, encoding='utf-8')

    # Act
    result = prompt_service.generate_first_prompt(countries, regulations)

    # Assert
    assert result == expected

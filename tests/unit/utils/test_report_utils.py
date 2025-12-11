"""report_utils の単体テスト。"""

from pathlib import Path

import pytest
import pytest_mock

from src.exceptions import ResourceNotFoundError
from src.utils.report_utils import PromptGenerator


@pytest.fixture
def template_path(tmp_path: Path) -> Path:
    """テンプレートファイルのパスを返すフィクスチャ。"""
    return tmp_path / 'template.md'


@pytest.fixture
def generator(mocker: pytest_mock.MockerFixture, template_path: Path) -> PromptGenerator:
    """PromptGeneratorインスタンスを返すフィクスチャ。"""
    prompt_dir = template_path.parent
    prompt_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch.object(PromptGenerator, '_prompt_dir', prompt_dir)
    return PromptGenerator()


@pytest.mark.asyncio
async def test_テンプレートファイルの読み込みが成功する(
    generator: PromptGenerator, template_path: Path
) -> None:
    # Arrange
    template_content = 'Template content'
    template_path.write_text(template_content, encoding='utf-8')

    # Act
    result = generator.load_template(template_path)

    # Assert
    assert result == template_content


@pytest.mark.asyncio
async def test_テンプレートファイルが存在しない場合にResourceNotFoundErrorを発生させる(
    generator: PromptGenerator, template_path: Path
) -> None:
    # Arrange
    # template_pathは存在しない

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match='Prompt template file not found'):
        generator.load_template(template_path)


@pytest.mark.asyncio
async def test_プロンプト名を取得できる(generator: PromptGenerator, template_path: Path) -> None:
    # Arrange
    template_path.write_text('Template content', encoding='utf-8')

    # Act
    result = generator.get_name()

    # Assert
    assert result == 'template'


@pytest.mark.parametrize(
    ('countries', 'regulations', 'expected'),
    [
        (['Japan', 'USA'], ['GDPR', 'CCPA'], 'Countries:\nJapan\nUSA\n\nRegulations:\nGDPR\nCCPA'),
        ([], [], 'Countries:\n\n\nRegulations:\n'),
        (['Japan', 'USA'], [], 'Countries:\nJapan\nUSA\n\nRegulations:\n'),
        ([], ['GDPR', 'CCPA'], 'Countries:\n\n\nRegulations:\nGDPR\nCCPA'),
    ],
)
@pytest.mark.asyncio
async def test_プロンプト生成が成功する(
    generator: PromptGenerator,
    template_path: Path,
    countries: list[str],
    regulations: list[str],
    expected: str,
) -> None:
    # Arrange
    template_content = 'Countries:\n${COUNTRY}\n\nRegulations:\n${REGULATION}'
    template_path.write_text(template_content, encoding='utf-8')

    # Act
    result = generator.generate_first_prompt(countries, regulations)

    # Assert
    assert result == expected

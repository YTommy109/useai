"""PreviewPromptUseCase の単体テスト。"""

from unittest.mock import Mock

import pytest

from src.services.prompt_service import PromptService
from src.usecases.preview_prompt import PreviewPromptUseCase


@pytest.fixture
def mock_prompt_service() -> Mock:
    return Mock(spec=PromptService)


@pytest.fixture
def usecase(mock_prompt_service: Mock) -> PreviewPromptUseCase:
    return PreviewPromptUseCase(mock_prompt_service)


@pytest.mark.asyncio
async def test_executeがプロンプトHTMLと国名リストと規制名リストを返す(
    usecase: PreviewPromptUseCase,
    mock_prompt_service: Mock,
) -> None:
    # Arrange
    countries = ['日本', 'アメリカ']
    regulations = ['GDPR', 'CCPA']
    prompt_text = '# Test Prompt\n\nCountries:\n日本\nアメリカ\n\nRegulations:\nGDPR\nCCPA'
    expected_html = (
        '<h1>Test Prompt</h1>\n<p>Countries:\n日本\nアメリカ</p>\n<p>Regulations:\nGDPR\nCCPA</p>'
    )

    mock_prompt_service.generate_first_prompt.return_value = prompt_text

    # Act
    prompt_html, result_countries, result_regulations = await usecase.execute(
        countries, regulations
    )

    # Assert
    assert prompt_html == expected_html
    assert result_countries == countries
    assert result_regulations == regulations
    mock_prompt_service.generate_first_prompt.assert_called_once_with(countries, regulations)


@pytest.mark.asyncio
async def test_executeが空のリストでも動作する(
    usecase: PreviewPromptUseCase,
    mock_prompt_service: Mock,
) -> None:
    # Arrange
    countries: list[str] = []
    regulations: list[str] = []
    prompt_text = 'Empty prompt'

    mock_prompt_service.generate_first_prompt.return_value = prompt_text

    # Act
    prompt_html, result_countries, result_regulations = await usecase.execute(
        countries, regulations
    )

    # Assert
    assert prompt_html == '<p>Empty prompt</p>'
    assert result_countries == []
    assert result_regulations == []


@pytest.mark.asyncio
async def test_executeがMarkdownを正しくHTMLに変換する(
    usecase: PreviewPromptUseCase,
    mock_prompt_service: Mock,
) -> None:
    # Arrange
    countries = ['日本']
    regulations = ['GDPR']
    prompt_text = '**Bold** and *italic* text'

    mock_prompt_service.generate_first_prompt.return_value = prompt_text

    # Act
    prompt_html, _, _ = await usecase.execute(countries, regulations)

    # Assert
    assert '<strong>Bold</strong>' in prompt_html
    assert '<em>italic</em>' in prompt_html

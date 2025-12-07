"""report_utils の単体テスト。"""

from pathlib import Path

import pytest
import pytest_mock

from src.exceptions import ResourceNotFoundError
from src.utils.report_utils import PromptGenerator


class TestPromptGenerator:
    """PromptGenerator のテストクラス。"""

    def test_テンプレートファイルの読み込みが成功する(
        self, mocker: pytest_mock.MockerFixture, tmp_path: Path
    ) -> None:
        # Arrange
        template_path = tmp_path / 'template.md'
        template_content = 'Template content'
        template_path.write_text(template_content, encoding='utf-8')

        # template_pathをモック
        mocker.patch.object(PromptGenerator, 'template_path', template_path)
        generator = PromptGenerator()

        # Act
        result = generator.load_template()

        # Assert
        assert result == template_content

    def test_テンプレートファイルが存在しない場合にResourceNotFoundErrorを発生させる(
        self, mocker: pytest_mock.MockerFixture, tmp_path: Path
    ) -> None:
        # Arrange
        template_path = tmp_path / 'nonexistent.md'
        # template_pathをモック
        mocker.patch.object(PromptGenerator, 'template_path', template_path)
        generator = PromptGenerator()

        # Act & Assert
        with pytest.raises(ResourceNotFoundError, match='Prompt template file not found'):
            generator.load_template()

    def test_プロンプト生成が成功する(
        self, mocker: pytest_mock.MockerFixture, tmp_path: Path
    ) -> None:
        # Arrange
        template_content = 'Countries:\n${COUNTRY}\n\nRegulations:\n${REGULATION}'
        template_path = tmp_path / 'template.md'
        template_path.write_text(template_content, encoding='utf-8')

        # template_pathをモック
        mocker.patch.object(PromptGenerator, 'template_path', template_path)
        generator = PromptGenerator()
        countries = ['Japan', 'USA']
        regulations = ['GDPR', 'CCPA']

        # Act
        result = generator.generate(countries, regulations)

        # Assert
        expected = 'Countries:\nJapan\nUSA\n\nRegulations:\nGDPR\nCCPA'
        assert result == expected

    def test_空のリストでプロンプト生成が成功する(
        self, mocker: pytest_mock.MockerFixture, tmp_path: Path
    ) -> None:
        # Arrange
        template_content = 'Countries:\n${COUNTRY}\n\nRegulations:\n${REGULATION}'
        template_path = tmp_path / 'template.md'
        template_path.write_text(template_content, encoding='utf-8')

        # template_pathをモック
        mocker.patch.object(PromptGenerator, 'template_path', template_path)
        generator = PromptGenerator()

        # Act
        result = generator.generate([], [])

        # Assert
        expected = 'Countries:\n\n\nRegulations:\n'
        assert result == expected

    def test_国のみでプロンプト生成が成功する(
        self, mocker: pytest_mock.MockerFixture, tmp_path: Path
    ) -> None:
        # Arrange
        template_content = 'Countries:\n${COUNTRY}\n\nRegulations:\n${REGULATION}'
        template_path = tmp_path / 'template.md'
        template_path.write_text(template_content, encoding='utf-8')

        # template_pathをモック
        mocker.patch.object(PromptGenerator, 'template_path', template_path)
        generator = PromptGenerator()
        countries = ['Japan', 'USA']

        # Act
        result = generator.generate(countries, [])

        # Assert
        expected = 'Countries:\nJapan\nUSA\n\nRegulations:\n'
        assert result == expected

    def test_規制のみでプロンプト生成が成功する(
        self, mocker: pytest_mock.MockerFixture, tmp_path: Path
    ) -> None:
        # Arrange
        template_content = 'Countries:\n${COUNTRY}\n\nRegulations:\n${REGULATION}'
        template_path = tmp_path / 'template.md'
        template_path.write_text(template_content, encoding='utf-8')

        # template_pathをモック
        mocker.patch.object(PromptGenerator, 'template_path', template_path)
        generator = PromptGenerator()
        regulations = ['GDPR', 'CCPA']

        # Act
        result = generator.generate([], regulations)

        # Assert
        expected = 'Countries:\n\n\nRegulations:\nGDPR\nCCPA'
        assert result == expected

"""テンプレートユーティリティの単体テスト。"""

from fastapi.templating import Jinja2Templates

from src.utils.template_utils import get_templates


def test_get_templatesがJinja2Templatesインスタンスを返す() -> None:
    # Act
    templates = get_templates()

    # Assert
    assert templates is not None
    assert isinstance(templates, Jinja2Templates)
    assert 'datetimeformat' in templates.env.filters


def test_get_templatesがdatetimeformatフィルターを登録している() -> None:
    # Act
    templates = get_templates()

    # Assert
    assert callable(templates.env.filters['datetimeformat'])

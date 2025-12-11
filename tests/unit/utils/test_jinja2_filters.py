"""Jinja2フィルターの単体テスト。"""

from datetime import datetime

import pytest

from src.utils.jinja2_filters import datetimeformat


@pytest.mark.parametrize(
    ('dt', 'expected'),
    [
        (datetime(2023, 1, 1, 0, 0, 0), '2023/01/01 00:00:00'),
        (datetime(2023, 12, 31, 23, 59, 59), '2023/12/31 23:59:59'),
        (datetime(2024, 2, 29, 12, 30, 45), '2024/02/29 12:30:45'),
    ],
)
def test_datetimeformatが正しくフォーマットする(dt: datetime, expected: str) -> None:
    # Act
    result = datetimeformat(dt)

    # Assert
    assert result == expected

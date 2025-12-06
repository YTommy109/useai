"""レポート生成関連のユーティリティ関数。

このモジュールは、レポート生成に関連する純粋関数を提供します。
"""

import random


def generate_prompt_text(countries: list[str], regulations: list[str]) -> str:
    """プロンプトテキストを生成する。

    Args:
        countries: 選択された国名のリスト。
        regulations: 選択された規制名のリスト。

    Returns:
        str: 生成されたプロンプトテキスト。
    """
    prompt_lines = [
        'ゴール: これはダミーのプロンプトです。',
        '',
        'ヘッダー部: プロンプトヘッダー部です。',
        '',
        '条件部:',
        '国:',
    ]
    for country in countries:
        prompt_lines.append(f'- {country}')

    prompt_lines.append('')
    prompt_lines.append('法規:')
    for regulation in regulations:
        prompt_lines.append(f'- {regulation}')

    prompt_lines.append('')
    prompt_lines.append('詳細: ここは詳細が入ります。')

    return '\n'.join(prompt_lines)


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

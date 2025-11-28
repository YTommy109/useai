"""フロントエンドアセット(CSS/JS)をダウンロードするスクリプト。

このスクリプトは、CDN から必要なフロントエンドライブラリをダウンロードし、
static/vendor/ ディレクトリに配置します。
"""

import urllib.request
from pathlib import Path

# ダウンロードするアセットの定義
ASSETS = [
    {
        'url': 'https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css',
        'path': 'static/vendor/css/pico.min.css',
    },
    {
        'url': 'https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js',
        'path': 'static/vendor/js/htmx.min.js',
    },
]


def download_assets() -> None:
    """アセットをダウンロードして配置する。"""
    for asset in ASSETS:
        path = Path(asset['path'])
        path.parent.mkdir(parents=True, exist_ok=True)

        print(f'Downloading: {asset["url"]}')
        urllib.request.urlretrieve(asset['url'], path)
        print(f'  -> Saved to: {asset["path"]}')

    print('\nAll assets downloaded successfully!')


if __name__ == '__main__':
    download_assets()

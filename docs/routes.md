# ルーティング一覧

アプリケーションで定義されているエンドポイント（パス）の一覧です。

## ページ (Pages)

| メソッド | パス | 説明 | 定義ファイル |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | トップページ（レポート一覧とメインUI）を表示する | `src/routers/pages.py` |

## レポート (Reports)

ベースパス: `/reports`

| メソッド | パス | 説明 | 定義ファイル |
| :--- | :--- | :--- | :--- |
| `GET` | `/reports/new` | 新規作成インターフェースを表示する | `src/routers/reports.py` |
| `POST` | `/reports/new/interface` | 選択された国・規制に基づいて文書生成し、UIを更新する | `src/routers/reports.py` |
| `POST` | `/reports` | レポートを作成する | `src/routers/reports.py` |
| `GET` | `/reports` | レポート一覧を取得する | `src/routers/reports.py` |
| `POST` | `/reports/prompt/preview` | プロンプトのプレビューを取得する | `src/routers/reports.py` |
| `GET` | `/reports/{report_id}/preview` | レポートのプレビュー（詳細）を表示する | `src/routers/reports.py` |
| `GET` | `/reports/{report_id}/download_csv` | レポートをCSV形式でダウンロードする | `src/routers/reports.py` |
| `GET` | `/reports/{report_id}/download_excel` | レポートをExcel形式でダウンロードする | `src/routers/reports.py` |

## 管理画面 (Admin)

ベースパス: `/admin`

| メソッド | パス | 説明 | 定義ファイル |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/` | 管理ダッシュボードを表示する | `src/routers/admin.py` |
| `POST` | `/admin/countries/import` | CSVから国データをインポートする | `src/routers/admin.py` |
| `POST` | `/admin/regulations/import` | CSVから規制データをインポートする | `src/routers/admin.py` |

## その他

| メソッド | パス | 説明 | 定義ファイル |
| :--- | :--- | :--- | :--- |
| `GET` | `/static` | 静的ファイル配信 | `src/main.py` |

# useai

FastAPIとHTMXを使用した軽量AIウェブアプリケーション

## 概要

このプロジェクトは、FastAPI、HTMX、Pico CSSを使用して構築された軽量なウェブアプリケーションです。国と規制を選択し、LLMを使用してテーブルデータを生成します。

## 必要要件

- Python 3.12以上
- pip（Pythonパッケージマネージャー）

## セットアップ

### Windows

1. リポジトリをクローン：
```cmd
git clone <repository-url>
cd useai
```

2. セットアップスクリプトを実行：
```cmd
setup.bat
```

**開発環境の場合:**
```cmd
REM 1. uvのインストール
pip install uv

REM 2. 仮想環境の作成
uv venv -p 3.12

REM 3. 開発依存関係を含めてインストール
uv sync --extra dev

REM 4. データディレクトリの作成
mkdir data

REM 5. アセットのダウンロード
task download-assets

REM 6. データベースマイグレーション
task migrate-apply
```

### Linux / macOS

1. リポジトリをクローン：
```bash
git clone <repository-url>
cd useai
```

2. セットアップスクリプトを実行：
```bash
chmod +x setup.sh
./setup.sh
```

**開発環境の場合:**
```bash
# 1. uvのインストール
pip3 install uv

# 2. 仮想環境の作成
uv venv -p 3.12

# 3. 開発依存関係を含めてインストール
uv sync --extra dev

# 4. データディレクトリの作成
mkdir -p data

# 5. アセットのダウンロード
task download-assets

# 6. データベースマイグレーション
task migrate-apply
```

## 使い方

### 本番サーバーの起動

```bash
# 仮想環境をアクティベート（Windows）
.venv\Scripts\activate

# 仮想環境をアクティベート（Linux/macOS）
source .venv/bin/activate

# 本番サーバーを起動
task prod
```

または、仮想環境をアクティベートせずに実行：
```bash
uv run task prod
```

ブラウザで http://localhost:8000 にアクセスしてください。

### 開発サーバーの起動

開発環境では、以下のコマンドで開発サーバーを起動できます：

```bash
# 仮想環境をアクティベート
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 開発サーバーを起動（ホットリロード有効）
task dev
```

## 開発

### テストの実行

```bash
# すべてのテストを実行
task test-all

# 単体テストのみ
task test-ut

# 統合テストのみ
task test-it

# カバレッジ付きでテスト
task coverage
```

### コード品質チェック

```bash
# Lintとフォーマット
task lint

# ruffのみ
task ruff

# mypyのみ
task mypy

# vultureのみ
task vulture
```

### データベースマイグレーション

```bash
# マイグレーションを適用
task migrate-apply

# マイグレーション履歴を表示
task migrate-history

# 1つ前のマイグレーションに戻す
task migrate-downgrade
```

## プロジェクト構造

```
useai/
├── src/                    # アプリケーションソースコード
│   ├── db/                 # データベース関連
│   │   ├── models.py       # SQLModelモデル
│   │   ├── repository.py   # リポジトリパターン
│   │   └── service.py      # ビジネスロジック
│   ├── routers/            # FastAPIルーター
│   ├── templates/          # Jinja2テンプレート
│   │   └── components/     # 再利用可能なコンポーネント
│   └── main.py             # アプリケーションエントリーポイント
├── tests/                  # テストコード
│   ├── unit/               # 単体テスト
│   └── integration/        # 統合テスト
├── migrations/             # Alembicマイグレーション
├── static/                 # 静的ファイル（CSS、JS）
├── data/                   # データファイル（SQLite DB、CSV）
├── setup.bat               # Windowsセットアップスクリプト
├── setup.sh                # Linux/macOSセットアップスクリプト
└── pyproject.toml          # プロジェクト設定
```

## 技術スタック

- **バックエンド**: FastAPI, SQLModel, Alembic
- **フロントエンド**: HTMX, Pico CSS
- **テンプレート**: Jinja2
- **データベース**: SQLite (開発), PostgreSQL対応可能
- **テスト**: pytest, pytest-asyncio
- **コード品質**: ruff, mypy, vulture

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。


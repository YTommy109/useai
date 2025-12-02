#!/bin/bash
set -e

echo "========================================"
echo "useai プロジェクト初期化スクリプト"
echo "========================================"
echo ""

# Pythonのバージョンチェック
echo "[0/6] 環境をチェックしています..."
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python 3がインストールされていません"
    echo "Python 3.12以上をインストールしてください"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Pythonバージョン: $PYTHON_VERSION"

# バージョン番号の抽出と確認
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 12 ]); then
    echo "エラー: Python 3.12以上が必要です（現在: $PYTHON_VERSION）"
    exit 1
fi
echo ""

# 1. uvのインストール確認とインストール
echo "[1/6] uvをインストールしています..."
pip3 install uv
echo ""

# 2. 仮想環境の作成
echo "[2/6] 仮想環境を作成しています..."
if [ -d ".venv" ]; then
    echo "既存の仮想環境が見つかりました。スキップします。"
else
    uv venv -p 3.12
fi
echo ""

# 3. 依存関係のインストール
echo "[3/6] 依存関係をインストールしています..."
uv sync
echo ""

# 4. データディレクトリの作成
echo "[4/6] データディレクトリを作成しています..."
mkdir -p data
echo ""

# 5. フロントエンドアセットのダウンロード
echo "[5/6] フロントエンドアセットをダウンロードしています..."
uv run python scripts/download_assets.py
echo ""

# 6. データベースマイグレーション
echo "[6/6] データベースを初期化しています..."
uv run alembic upgrade head
echo ""

echo "========================================"
echo "セットアップが完了しました！"
echo "========================================"
echo ""
echo "次のコマンドでアプリケーションを起動できます："
echo "  source .venv/bin/activate"
echo "  task prod"
echo ""
echo "または、仮想環境をアクティベートせずに実行："
echo "  uv run task prod"
echo ""

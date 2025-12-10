@echo off
setlocal enabledelayedexpansion

echo ========================================
echo useai プロジェクト初期化スクリプト
echo ========================================
echo.

REM Pythonのバージョンチェック
echo [0/6] 環境をチェックしています...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo エラー: Pythonがインストールされていません
    echo Python 3.12以上をインストールしてください
    pause
    exit /b 1
)

REM Pythonバージョンの取得と確認
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Pythonバージョン: %PYTHON_VERSION%

REM バージョン番号の抽出（3.12.0 -> 3.12）
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo エラー: Python 3.12以上が必要です（現在: %PYTHON_VERSION%）
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 12 (
    echo エラー: Python 3.12以上が必要です（現在: %PYTHON_VERSION%）
    pause
    exit /b 1
)
echo.

REM 1. uvのインストール確認とインストール
echo [1/6] uvをインストールしています...
pip install uv
if %ERRORLEVEL% neq 0 (
    echo エラー: uvのインストールに失敗しました
    pause
    exit /b 1
)
echo.

REM 2. 仮想環境の作成
echo [2/6] 仮想環境を作成しています...
if exist .venv (
    echo 既存の仮想環境が見つかりました。スキップします。
) else (
    uv venv -p 3.12
    if %ERRORLEVEL% neq 0 (
        echo エラー: 仮想環境の作成に失敗しました
        pause
        exit /b 1
    )
)
echo.

REM 3. 依存関係のインストール
echo [3/6] 依存関係をインストールしています...
uv sync
if %ERRORLEVEL% neq 0 (
    echo エラー: 依存関係のインストールに失敗しました
    pause
    exit /b 1
)
echo.

REM 4. データディレクトリの作成
echo [4/7] データディレクトリを作成しています...
if not exist data mkdir data
echo.

REM 5. 設定ファイルのコピー
echo [5/7] 設定ファイルをコピーしています...
if not exist data\csv (
    xcopy /E /I /Y config\csv.example data\csv
) else (
    echo data\csv ディレクトリが既に存在します。スキップします。
)
if not exist data\prompt (
    xcopy /E /I /Y config\prompt.example data\prompt
) else (
    echo data\prompt ディレクトリが既に存在します。スキップします。
)
echo.

REM 6. フロントエンドアセットのダウンロード
echo [6/7] フロントエンドアセットをダウンロードしています...
uv run python scripts\download_assets.py
if %ERRORLEVEL% neq 0 (
    echo エラー: アセットのダウンロードに失敗しました
    pause
    exit /b 1
)
echo.

REM 7. データベースマイグレーション
echo [7/7] データベースを初期化しています...
uv run alembic upgrade head
if %ERRORLEVEL% neq 0 (
    echo エラー: データベースマイグレーションに失敗しました
    pause
    exit /b 1
)
echo.

echo ========================================
echo セットアップが完了しました！
echo ========================================
echo.
echo 次のコマンドでアプリケーションを起動できます：
echo   .venv\Scripts\activate
echo   task prod
echo.
echo または、仮想環境をアクティベートせずに実行：
echo   uv run task prod
echo.
pause

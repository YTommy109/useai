import os
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Country, Regulation


@pytest.mark.asyncio
async def test_管理ダッシュボードの統計が表示される(
    client: TestClient, session: AsyncSession
) -> None:
    # Arrange
    # conftestで既に2件ずつ追加されているので、追加のデータは不要

    # Act
    response = client.get('/admin')

    # Assert
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, 'html.parser')
    country_count_elem = soup.select_one('#country-count')
    regulation_count_elem = soup.select_one('#regulation-count')

    assert country_count_elem is not None
    assert regulation_count_elem is not None
    assert country_count_elem.text == '2'
    assert regulation_count_elem.text == '2'


@pytest.mark.asyncio
async def test_国データをインポートできる(
    client: TestClient, session: AsyncSession, tmp_path: Path
) -> None:
    # Arrange: 実際のCSVファイルを作成
    csv_dir = tmp_path / 'data' / 'csv'
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_file = csv_dir / 'countries.csv'
    csv_file.write_text('name,continent\n新規国1,欧州\n新規国2,アジア', encoding='utf-8')

    # エンドポイントが参照するパスにファイルを作成するため、カレントディレクトリを変更
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Act
        response = client.post('/admin/import/countries')
    finally:
        os.chdir(original_cwd)

    # Assert
    assert response.status_code == 200
    assert response.text == '2'

    # Verify database state
    countries = await session.exec(select(Country))
    results = countries.all()
    assert len(results) == 2
    names = [r.name for r in results]
    assert '新規国1' in names
    assert '新規国2' in names


@pytest.mark.asyncio
async def test_規制データをインポートできる(
    client: TestClient, session: AsyncSession, tmp_path: Path
) -> None:
    # Arrange: 実際のCSVファイルを作成
    csv_dir = tmp_path / 'data' / 'csv'
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_file = csv_dir / 'regulations.csv'
    csv_file.write_text('name\n新規規制1\n新規規制2', encoding='utf-8')

    # エンドポイントが参照するパスにファイルを作成するため、カレントディレクトリを変更
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Act
        response = client.post('/admin/import/regulations')
    finally:
        os.chdir(original_cwd)

    # Assert
    assert response.status_code == 200
    assert response.text == '2'

    # DBの内容を検証
    result = await session.exec(select(Regulation))
    regulations = result.all()
    assert len(regulations) == 2
    names = [r.name for r in regulations]
    assert '新規規制1' in names
    assert '新規規制2' in names


@pytest.mark.parametrize(
    'endpoint',
    ['/admin/import/countries', '/admin/import/regulations'],
)
@pytest.mark.asyncio
async def test_インポート_ファイルが存在しない場合404(
    client: TestClient, endpoint: str, tmp_path: Path
) -> None:
    # Arrange: ファイルが存在しない状態にする
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Act
        response = client.post(endpoint)
    finally:
        os.chdir(original_cwd)

    # Assert
    assert response.status_code == 404
    assert 'CSV file not found' in response.text


@pytest.mark.parametrize(
    ('endpoint', 'filename', 'model_class', 'header'),
    [
        ('/admin/import/countries', 'countries.csv', Country, 'name,continent\n'),
        ('/admin/import/regulations', 'regulations.csv', Regulation, 'name\n'),
    ],
)
@pytest.mark.asyncio
async def test_インポート_空のCSVの場合0件(
    client: TestClient,
    session: AsyncSession,
    tmp_path: Path,
    endpoint: str,
    filename: str,
    model_class: type[SQLModel],
    header: str,
) -> None:
    # Arrange: ヘッダーのみのCSVファイルを作成
    csv_dir = tmp_path / 'data' / 'csv'
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_file = csv_dir / filename
    csv_file.write_text(header, encoding='utf-8')

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Act
        response = client.post(endpoint)
    finally:
        os.chdir(original_cwd)

    # Assert
    assert response.status_code == 200
    assert response.text == '0'

    # DBが空であることを確認
    result = await session.exec(select(model_class))
    items = result.all()
    assert len(items) == 0

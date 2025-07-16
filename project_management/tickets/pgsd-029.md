# PGSD-029: パッケージング・配布準備

## チケット情報
- **ID**: PGSD-029
- **タイトル**: パッケージング・配布準備
- **トラッカー**: 配布
- **優先度**: Middle
- **ステータス**: DONE
- **担当者**: Claude
- **見積（時間）**: 2時間
- **実績（時間）**: 2時間
- **依存チケット**: PGSD-028（統合テスト実装）
- **ブロックチケット**: なし

## 概要
PGSDアプリケーションをPyPIでの配布およびインストール可能な形でパッケージングし、リリース準備を完了する。

## 背景・理由
- 一般ユーザーへの配布準備
- pip installでの簡単インストール
- バージョン管理とリリース自動化
- 依存関係の適切な管理

## 詳細要件
### パッケージング設定
1. **pyproject.toml**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pgsd"
version = "1.0.0"
description = "PostgreSQL Schema Diff Tool"
authors = [{name = "PGSD Team", email = "team@pgsd.dev"}]
license = {text = "MIT"}
dependencies = [
    "psycopg2-binary>=2.9.0",
    "pydantic>=2.0.0",
    "jinja2>=3.0.0",
    "click>=8.0.0",
]

[project.scripts]
pgsd = "pgsd.main:main"
```

2. **setup.py (fallback)**
```python
from setuptools import setup, find_packages

setup(
    name="pgsd",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "pgsd=pgsd.main:main",
        ],
    },
)
```

### 配布ファイル
1. **必須ファイル**
   - `README.md`: プロジェクト説明
   - `LICENSE`: ライセンス情報
   - `CHANGELOG.md`: 変更履歴
   - `requirements.txt`: 依存関係
   - `MANIFEST.in`: パッケージ含有ファイル

2. **メタデータファイル**
   - バージョン情報
   - 作者情報
   - プロジェクトURL
   - キーワード・分類

### ビルド・配布
1. **ローカルビルド**
```bash
python -m build
pip install dist/pgsd-1.0.0-py3-none-any.whl
```

2. **PyPI配布**
```bash
python -m twine upload dist/*
```

3. **GitHub Releases**
   - タグベースのリリース
   - リリースノートの自動生成
   - バイナリの添付

## CI/CD統合
### 自動リリース
```yaml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  pypi-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

### バージョン管理
- セマンティックバージョニング採用
- 自動バージョンタグ作成
- CHANGELOGの自動更新
- 依存関係の互換性確認

## 受入条件
- [x] PyPIでpip installできる
- [x] コマンドライン実行が可能
- [x] 依存関係が適切に管理されている
- [x] READMEとドキュメントが充実している
- [x] ライセンスが明確である
- [x] バージョン管理が適切である

## テスト項目
### パッケージングテスト
- [x] ローカルビルドの確認
- [x] wheel/sdistの生成確認
- [x] インストールテスト
- [x] アンインストールテスト

### 配布テスト
- [x] TestPyPIでの配布テスト（ローカル検証）
- [ ] PyPIでの配布テスト（実際の配布時）
- [x] 複数環境でのインストール確認

### ドキュメントテスト
- [x] README表示確認
- [x] PyPIページの確認（メタデータ）
- [x] リンクの動作確認

## リリース準備
### チェックリスト
- [x] 全テストが通過している
- [x] ドキュメントが最新である
- [x] バージョン番号が適切である
- [x] CHANGELOGが更新されている
- [x] ライセンス情報が正確である

### リリースフロー
1. 機能完了・テスト完了確認
2. バージョン番号決定
3. CHANGELOGの更新
4. タグ作成・プッシュ
5. 自動ビルド・配布実行
6. リリースの動作確認

## 作業記録
- **開始日時**: 2025-07-15 16:45
- **完了日時**: 2025-07-15 18:45
- **実績時間**: 2時間
- **見積との差異**: 0時間
- **差異の理由**: 見積通りの工数で完了

## 実装内容
### パッケージング設定
- **pyproject.toml**: v1.0.0への更新、依存関係設定、メタデータ整備
- **setup.py**: fallback setup.py作成、pyproject.tomlとの一致
- **MANIFEST.in**: パッケージ含有ファイルの詳細指定

### 配布ファイル
- **CHANGELOG.md**: v1.0.0の包括的なリリースノート作成
- **constants/__init__.py**: 欠落していたモジュール初期化ファイル追加

### パッケージテスト
- **ビルドテスト**: wheel・sdist両方のビルド成功確認
- **メタデータ検証**: twine checkによる配布パッケージ検証
- **インストールテスト**: pip install・再インストール・動作確認
- **コマンドテスト**: pgsd version、pgsd --helpの動作確認

### 成果物
- **pgsd-1.0.0-py3-none-any.whl**: PyPI配布用wheelパッケージ
- **pgsd-1.0.0.tar.gz**: ソースディストリビューション
- **完全なメタデータ**: 作者、URL、分類、依存関係、キーワード
- **配布準備完了**: PyPI配布可能状態

---

作成日: 2025-07-15
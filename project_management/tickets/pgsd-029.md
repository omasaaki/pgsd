# PGSD-029: パッケージング・配布準備

## チケット情報
- **ID**: PGSD-029
- **タイトル**: パッケージング・配布準備
- **トラッカー**: 配布
- **優先度**: Middle
- **ステータス**: TODO
- **担当者**: 未定
- **見積（時間）**: 2時間
- **実績（時間）**: -
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
- [ ] PyPIでpip installできる
- [ ] コマンドライン実行が可能
- [ ] 依存関係が適切に管理されている
- [ ] READMEとドキュメントが充実している
- [ ] ライセンスが明確である
- [ ] バージョン管理が適切である

## テスト項目
### パッケージングテスト
- [ ] ローカルビルドの確認
- [ ] wheel/sdistの生成確認
- [ ] インストールテスト
- [ ] アンインストールテスト

### 配布テスト
- [ ] TestPyPIでの配布テスト
- [ ] PyPIでの配布テスト
- [ ] 複数環境でのインストール確認

### ドキュメントテスト
- [ ] README表示確認
- [ ] PyPIページの確認
- [ ] リンクの動作確認

## リリース準備
### チェックリスト
- [ ] 全テストが通過している
- [ ] ドキュメントが最新である
- [ ] バージョン番号が適切である
- [ ] CHANGELOGが更新されている
- [ ] ライセンス情報が正確である

### リリースフロー
1. 機能完了・テスト完了確認
2. バージョン番号決定
3. CHANGELOGの更新
4. タグ作成・プッシュ
5. 自動ビルド・配布実行
6. リリースの動作確認

## 作業記録
- **開始日時**: 未定
- **完了日時**: 未定
- **実績時間**: 未定
- **見積との差異**: 未定
- **差異の理由**: 未定

---

作成日: 2025-07-15
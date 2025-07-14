# CI/CD詳細設計書

## 概要
GitHub ActionsによるCI/CDパイプラインの詳細実装設計

## 1. ワークフローファイル詳細設計

### 1.1 Pull Request CI (ci.yml)

```yaml
name: CI

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      - name: Run flake8
        run: flake8 src tests
      - name: Run black
        run: black --check src tests
      - name: Run mypy
        run: mypy src

  test:
    name: Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macOS-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-${{ matrix.python-version }}-pip-${{ hashFiles('**/requirements*.txt') }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml --cov-report=html
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install security tools
        run: |
          python -m pip install --upgrade pip
          pip install safety bandit
      - name: Run safety check
        run: safety check
      - name: Run bandit
        run: bandit -r src/
```

### 1.2 Continuous Deployment (cd.yml)

```yaml
name: CD

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install -r requirements-dev.txt
      - name: Run full test suite
        run: pytest --cov=src --cov-fail-under=80

  build:
    name: Build Package
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Check package
        run: twine check dist/*
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  release:
    name: Release
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          draft: false
          prerelease: false
```

### 1.3 Security Workflow (security.yml)

```yaml
name: Security

on:
  schedule:
    - cron: '0 8 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  dependency-check:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety pip-audit
      - name: Run safety check
        run: safety check --json --output safety-report.json
      - name: Run pip-audit
        run: pip-audit --desc --output audit-report.json --format json
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            safety-report.json
            audit-report.json

  code-analysis:
    name: Static Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install analysis tools
        run: |
          python -m pip install --upgrade pip
          pip install bandit semgrep
      - name: Run bandit
        run: bandit -r src/ -f json -o bandit-report.json
      - name: Run semgrep
        run: semgrep --config=auto src/ --json --output=semgrep-report.json
      - name: Upload analysis reports
        uses: actions/upload-artifact@v3
        with:
          name: analysis-reports
          path: |
            bandit-report.json
            semgrep-report.json
```

## 2. 設定ファイル詳細

### 2.1 Dependabot設定 (.github/dependabot.yml)

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    reviewers:
      - "omasaaki"
    assignees:
      - "omasaaki"
    commit-message:
      prefix: "deps"
      include: "scope"
    open-pull-requests-limit: 5
    
  - package-ecosystem: "github-actions"
    directory: "/.github/workflows"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "ci"
      include: "scope"
```

### 2.2 Pull Request Template (.github/pull_request_template.md)

```markdown
## 概要
<!-- 変更内容の簡潔な説明 -->

## 変更種別
- [ ] 新機能
- [ ] バグ修正
- [ ] リファクタリング
- [ ] ドキュメント更新
- [ ] テスト追加・修正
- [ ] CI/CD改善

## チェックリスト
- [ ] テストが追加されている
- [ ] ドキュメントが更新されている
- [ ] CHANGELOG.mdが更新されている
- [ ] CI/CDが通っている

## 関連チケット
<!-- 関連するIssue番号 -->
Closes #XXX

## 動作確認
<!-- 動作確認方法と結果 -->

## レビューポイント
<!-- レビューで特に注意して見てほしい点 -->
```

### 2.3 Issue Template (.github/ISSUE_TEMPLATE/)

#### Bug Report (bug_report.yml)
```yaml
name: Bug Report
description: バグ報告
body:
  - type: markdown
    attributes:
      value: |
        バグ報告ありがとうございます。
        
  - type: textarea
    id: description
    attributes:
      label: 問題の説明
      description: 発生している問題を詳しく説明してください
    validations:
      required: true
      
  - type: textarea
    id: steps
    attributes:
      label: 再現手順
      description: 問題を再現するための手順
      placeholder: |
        1. ...
        2. ...
        3. ...
    validations:
      required: true
      
  - type: textarea
    id: expected
    attributes:
      label: 期待される動作
      description: 本来期待される動作
    validations:
      required: true
      
  - type: textarea
    id: environment
    attributes:
      label: 環境情報
      description: |
        - OS:
        - Python Version:
        - PGSD Version:
      render: markdown
    validations:
      required: true
```

## 3. 品質ゲート詳細設計

### 3.1 テストカバレッジ要件
```python
# pytest.ini
[tool:pytest]
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
    --strict-config
testpaths = tests
```

### 3.2 静的解析設定

#### flake8設定 (.flake8)
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .pytest_cache,
    .coverage,
    htmlcov,
    dist,
    build
per-file-ignores =
    tests/*:S101
```

#### mypy設定 (pyproject.toml)
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

### 3.3 セキュリティチェック設定

#### bandit設定 (.bandit)
```yaml
skips: []
tests: []
exclude_dirs:
  - /tests/
```

## 4. パフォーマンス最適化

### 4.1 キャッシュ戦略
- **pip依存関係**: requirements.txtハッシュベース
- **テスト結果**: pytest-cacheDirベース
- **静的解析**: ソースコードハッシュベース

### 4.2 並列実行最適化
- **テストマトリックス**: OS × Pythonバージョン
- **ジョブ分割**: lint/test/security並列実行
- **fail-fast**: 最初の失敗で即座に停止

### 4.3 実行時間目標
- **PRチェック**: 5分以内
- **フルテスト**: 15分以内
- **リリースビルド**: 10分以内

## 5. 監視・アラート

### 5.1 通知設定
- **Slack統合**: 失敗時の即座通知
- **Email**: セキュリティアラート
- **GitHub**: PR/Issue自動ラベリング

### 5.2 メトリクス収集
- **ビルド時間**: 履歴トラッキング
- **成功率**: 週次レポート
- **カバレッジ**: トレンド分析

## 6. 運用手順

### 6.1 緊急時対応
1. CI/CD無効化手順
2. ホットフィックス適用手順
3. ロールバック手順

### 6.2 定期メンテナンス
- **月次**: ワークフロー実行時間レビュー
- **四半期**: セキュリティ設定見直し
- **年次**: プラットフォーム/ツール更新

---

**実装ファイル:**
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `.github/workflows/security.yml`
- `.github/dependabot.yml`
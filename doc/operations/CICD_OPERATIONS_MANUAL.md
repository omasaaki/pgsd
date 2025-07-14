# CI/CD運用マニュアル

## 概要
このドキュメントは、PostgreSQL Schema Diff Tool (PGSD)プロジェクトのCI/CDパイプライン運用に関する包括的なガイドです。

## 目次
1. [CI/CDパイプライン概要](#cicdパイプライン概要)
2. [開発者向けガイド](#開発者向けガイド)
3. [ワークフロー詳細](#ワークフロー詳細)
4. [トラブルシューティング](#トラブルシューティング)
5. [パフォーマンス最適化](#パフォーマンス最適化)
6. [セキュリティ管理](#セキュリティ管理)
7. [リリース管理](#リリース管理)

---

## CI/CDパイプライン概要

### アーキテクチャ
```
Pull Request → CI Pipeline → Code Review → Merge → CD Pipeline → Release
```

### 主要コンポーネント
| ワークフロー | ファイル | トリガー | 目的 |
|-------------|----------|---------|------|
| CI | `.github/workflows/ci.yml` | PR/Push | 品質チェック |
| CD | `.github/workflows/cd.yml` | mainブランチ/タグ | ビルド・デプロイ |
| Security | `.github/workflows/security.yml` | 週次/手動 | セキュリティスキャン |

### 実行環境マトリックス
- **Python版**: 3.8, 3.9, 3.10, 3.11, 3.12
- **OS**: Ubuntu, Windows, macOS
- **総実行ジョブ数**: 最大15並列

---

## 開発者向けガイド

### 1. プルリクエスト作成フロー

#### 事前準備
```bash
# 1. 最新のmainブランチを取得
git checkout main
git pull origin main

# 2. 機能ブランチ作成
git checkout -b feature/PGSD-XXX-description

# 3. ローカル開発環境セットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

#### コーディング規約チェック
```bash
# 自動フォーマット適用
black src tests
isort src tests

# 静的解析実行
flake8 src tests
mypy src

# テスト実行
pytest --cov=src --cov-report=term-missing
```

#### プルリクエスト作成
1. **変更をコミット**
   ```bash
   git add .
   git commit -m "Add feature: PGSD-XXX description
   
   - Detailed change 1
   - Detailed change 2"
   ```

2. **ブランチをプッシュ**
   ```bash
   git push origin feature/PGSD-XXX-description
   ```

3. **GitHub UIでPR作成**
   - PRテンプレートに従って情報を記入
   - 関連チケット番号を記載
   - レビュアーを指定

### 2. CI/CD実行確認

#### GitHub ActionsでのCI実行確認
1. **PR作成直後にCIが自動実行**
   - 「Actions」タブで実行状況を確認
   - 全てのチェックが✅になるまで待機

2. **失敗時の対応**
   ```bash
   # ローカルで同じチェックを実行
   flake8 src tests           # 静的解析
   black --check src tests    # フォーマットチェック  
   mypy src                   # 型チェック
   pytest                     # テスト実行
   ```

#### CI実行時間目安
- **リンター**: 2-3分
- **テスト（単一環境）**: 3-5分
- **テスト（全マトリックス）**: 10-15分
- **セキュリティスキャン**: 5-8分

---

## ワークフロー詳細

### 1. CI Pipeline (ci.yml)

#### ジョブ構成
```yaml
jobs:
  lint:          # コード品質チェック
  test:          # マルチ環境テスト
  security:      # セキュリティスキャン
```

#### 品質ゲート
| チェック項目 | ツール | 基準 |
|-------------|--------|------|
| コードフォーマット | black | 100%準拠 |
| 静的解析 | flake8 | エラー0件 |
| 型チェック | mypy | エラー0件 |
| テストカバレッジ | pytest-cov | 40%以上 |
| セキュリティ | bandit | 重要度High以下 |

#### 実行コマンド例
```bash
# CIで実行される主要コマンド
flake8 src tests
black --check src tests
mypy src
pytest --cov=src --cov-report=xml --cov-report=html
bandit -r src/ -f json
safety check --json
```

### 2. CD Pipeline (cd.yml)

#### トリガー条件
- **mainブランチへのプッシュ**: テスト実行のみ
- **タグプッシュ (v*)**: フルリリースプロセス

#### リリースフロー
```
Test → Build → Package → GitHub Release → Artifacts Upload
```

#### パッケージ作成
```bash
# ローカルでの同等操作
python -m build
twine check dist/*
```

### 3. Security Pipeline (security.yml)

#### スキャン内容
- **依存関係脆弱性**: safety, pip-audit
- **コード解析**: bandit, semgrep  
- **シークレット検出**: trufflehog

#### 実行タイミング
- **週次**: 毎週月曜日 8:00 UTC
- **手動**: Actions画面から実行可能
- **依存関係変更時**: requirements*.txt更新時

---

## トラブルシューティング

### 1. よくあるCI失敗原因と対処法

#### flake8エラー
```bash
# エラー例
src/pgsd/module.py:10:80: E501 line too long (89 > 88 characters)

# 対処法
black src tests  # 自動修正
# または手動でコード修正
```

#### テスト失敗
```bash
# ローカルで詳細確認
pytest tests/test_specific.py -v --tb=long

# カバレッジ不足の場合
pytest --cov=src --cov-report=html
# htmlcov/index.html で詳細確認
```

#### インポートエラー
```bash
# パッケージインストール確認
pip install -e .
pip list | grep pgsd

# モジュールパス確認
python -c "import pgsd; print(pgsd.__file__)"
```

### 2. セキュリティスキャン警告対応

#### safety警告（依存関係脆弱性）
```bash
# 具体的な脆弱性確認
safety check --json --output safety-report.json

# 依存関係更新
pip-compile requirements.in
pip install -r requirements.txt
```

#### bandit警告（コードセキュリティ）
```bash
# 詳細レポート生成
bandit -r src/ -f json -o bandit-report.json

# 除外設定（必要に応じて）
# pyproject.toml [tool.bandit] セクションで設定
```

### 3. パフォーマンス問題

#### CI実行時間が長い
1. **キャッシュ効率確認**
   ```yaml
   # .github/workflows/ci.yml
   - name: Cache pip dependencies
     uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
   ```

2. **並列実行最適化**
   ```yaml
   strategy:
     matrix:
       python-version: ['3.8', '3.11']  # 必要最小限に絞る
     fail-fast: true  # 最初の失敗で停止
   ```

#### テスト実行時間短縮
```bash
# 高速テスト実行
pytest -x                    # 最初の失敗で停止
pytest -n auto              # 並列実行（pytest-xdist）
pytest --lf                 # 前回失敗分のみ
pytest -m "not slow"        # 重いテストをスキップ
```

---

## セキュリティ管理

### 1. シークレット管理

#### GitHub Secrets設定
| シークレット名 | 用途 | 設定場所 |
|---------------|------|----------|
| CODECOV_TOKEN | カバレッジレポート | Repository secrets |
| PYPI_TOKEN | PyPI公開（将来） | Repository secrets |

#### 設定手順
1. GitHub Repository → Settings → Secrets and variables → Actions
2. 「New repository secret」でシークレット追加
3. ワークフローファイルで参照: `${{ secrets.SECRET_NAME }}`

### 2. 脆弱性対応フロー

#### 依存関係脆弱性発見時
1. **影響範囲調査**
   ```bash
   safety check --json | jq '.vulnerabilities'
   pip-audit --desc --format json
   ```

2. **更新計画策定**
   - 脆弱性レベル評価（Critical/High/Medium/Low）
   - 互換性影響調査
   - テスト実行による動作確認

3. **更新実施**
   ```bash
   # 依存関係更新
   pip install --upgrade package_name
   pip freeze > requirements.txt
   
   # テスト実行
   pytest
   
   # PR作成
   git checkout -b security/update-dependencies
   git commit -m "Security: Update vulnerable dependencies"
   ```

### 3. セキュリティベストプラクティス

#### コードレビュー時チェック項目
- [ ] 機密情報のハードコーディングなし
- [ ] SQLインジェクション対策済み
- [ ] 入力値検証実装済み
- [ ] エラーメッセージに機密情報含まず
- [ ] ログ出力に機密情報含まず

#### ワークフロー設定
```yaml
# 最小権限の原則
permissions:
  contents: read
  security-events: write  # セキュリティレポート用のみ
```

---

## リリース管理

### 1. バージョニング戦略

#### セマンティックバージョニング
```
MAJOR.MINOR.PATCH (例: 1.2.3)
```

- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換性のある機能追加  
- **PATCH**: 後方互換性のあるバグ修正

#### タグ作成手順
```bash
# 1. バージョン更新
# pyproject.toml の version を更新

# 2. 変更をコミット
git add pyproject.toml
git commit -m "Bump version to 1.2.3"

# 3. タグ作成・プッシュ
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

### 2. リリースプロセス

#### 自動リリース (CDパイプライン)
1. **タグプッシュでトリガー**
2. **全テスト実行**
3. **パッケージビルド**
4. **GitHub Release作成**
5. **アーティファクト添付**

#### 手動確認項目
- [ ] CHANGELOGの更新
- [ ] ドキュメントの更新
- [ ] 移行ガイド（破壊的変更がある場合）
- [ ] リリースノートの作成

### 3. ホットフィックス手順

#### 緊急修正が必要な場合
```bash
# 1. リリースブランチから分岐
git checkout main
git checkout -b hotfix/v1.2.4

# 2. 修正実装
# バグ修正コード

# 3. テスト実行
pytest

# 4. バージョン更新
# pyproject.toml version: 1.2.4

# 5. PR作成・マージ
# 6. タグ作成
git tag -a v1.2.4 -m "Hotfix: Critical bug fix"
git push origin v1.2.4
```

---

## パフォーマンス最適化

### 1. CI実行時間短縮

#### キャッシュ戦略最適化
```yaml
# 効果的なキャッシュ設定例
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: |
      ~/.cache/pip
      ~/.cache/pre-commit
    key: ${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt', '.pre-commit-config.yaml') }}
    restore-keys: |
      ${{ runner.os }}-${{ matrix.python-version }}-
```

#### 並列実行最適化
```yaml
# ジョブ分割による高速化
jobs:
  lint:
    # 軽量チェックを最初に実行
  test-unit:
    # 単体テストのみ
  test-integration:
    # 統合テストのみ（依存関係多）
    needs: lint  # lintパス後に実行
```

### 2. ローカル開発効率化

#### Pre-commit hooks活用
```bash
# セットアップ
pre-commit install

# 手動実行
pre-commit run --all-files

# 特定フックのみ実行
pre-commit run black
```

#### 高速テスト実行
```bash
# テストファイル単位
pytest tests/test_specific.py

# マーカー利用
pytest -m unit          # 単体テストのみ
pytest -m "not slow"    # 重いテストを除外

# 並列実行
pytest -n auto          # CPU数に応じて並列実行
```

---

## 監視・アラート

### 1. CI/CD成功率監視

#### GitHub Insights活用
- **Actions** → **Workflow runs** で成功率確認
- 失敗率が10%を超えた場合は調査

#### 週次レビュー項目
- [ ] CI成功率（目標: 95%以上）
- [ ] 平均実行時間（目標: 15分以内）
- [ ] セキュリティスキャン結果
- [ ] 依存関係更新状況

### 2. 品質メトリクス

#### コードカバレッジ
- **現在**: 40%以上（基準値）
- **目標**: 80%以上（段階的に向上）

#### 技術債務管理
```bash
# 静的解析結果トレンド確認
flake8 src --statistics
mypy src --report coverage
```

---

## 緊急時対応

### 1. CI/CD無効化手順

#### 一時的無効化
```yaml
# ワークフローファイル先頭に追加
on:
  workflow_dispatch:  # 手動実行のみ許可
  # push:             # 自動実行を無効化
  # pull_request:     # 自動実行を無効化
```

#### 完全停止
1. GitHub Repository → Settings → Actions → General
2. 「Disable actions for this repository」を選択

### 2. ロールバック手順

#### GitHub Release削除
```bash
# タグ削除
git tag -d v1.2.3
git push origin --delete v1.2.3

# GitHub Release削除（UI操作）
# Releases → 該当バージョン → Delete release
```

#### 緊急パッチ適用
```bash
# 前バージョンから緊急ブランチ作成
git checkout v1.2.2
git checkout -b emergency/rollback-v1.2.3

# 修正適用
# ...

# 緊急リリース
git tag -a v1.2.3-hotfix.1 -m "Emergency rollback"
git push origin v1.2.3-hotfix.1
```

---

## 連絡先・サポート

### 技術サポート
- **GitHub Issues**: バグ報告・機能要求
- **Discussions**: 一般的な質問・議論

### 緊急連絡先
- **メンテナー**: @omasaaki
- **バックアップ**: GitHub Issues

---

## 更新履歴
- **2025-07-14**: 初版作成
- **YYYY-MM-DD**: 更新内容
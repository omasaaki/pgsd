# CI/CD パイプライン

## 概要
このドキュメントは PGSD プロジェクトの CI/CD パイプラインについて説明します。

## 🚀 クイックスタート

### 開発者向け
```bash
# 開発環境セットアップ
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .

# 品質チェック実行
flake8 src tests
black src tests  
pytest --cov=src
```

### CI/CD 確認
1. **Pull Request 作成** → 自動的に CI パイプライン実行
2. **Actions タブ** → 実行状況確認
3. **全チェック通過** → レビュー・マージ可能

## 📊 パイプライン概要

### ワークフロー構成
| ワークフロー | トリガー | 実行時間目安 | 目的 |
|-------------|---------|-------------|------|
| **CI** | PR/Push | 10-15分 | 品質チェック |
| **CD** | Main/Tag | 5-10分 | ビルド・リリース |
| **Security** | 週次/手動 | 5-8分 | セキュリティスキャン |

### 品質ゲート
- ✅ **コードフォーマット**: black, isort
- ✅ **静的解析**: flake8, mypy  
- ✅ **テスト**: pytest (カバレッジ 40%+)
- ✅ **セキュリティ**: bandit, safety

## 🔧 開発ワークフロー

### 1. ブランチ作成
```bash
git checkout main
git pull origin main
git checkout -b feature/PGSD-XXX-description
```

### 2. 開発・テスト
```bash
# コード実装
# ...

# ローカル品質チェック
pre-commit run --all-files
pytest
```

### 3. Pull Request
```bash
git push origin feature/PGSD-XXX-description
# GitHub UI で PR 作成
```

### 4. CI 実行確認
- **GitHub Actions** タブで進捗確認
- 失敗時は **Details** から詳細確認
- ローカルで同じチェックを実行して修正

## 🛠️ ローカル環境

### 必要ツール
```bash
# 基本ツール
pip install black flake8 mypy isort pytest pytest-cov

# セキュリティツール  
pip install safety bandit

# 自動化
pip install pre-commit
pre-commit install
```

### 推奨 VS Code 設定
```json
{
    "python.formatting.provider": "black",
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true
}
```

## 📈 メトリクス

### 現在の状況
- **テストカバレッジ**: 43% (目標: 80%)
- **CI成功率**: 95%+ (目標維持)
- **平均実行時間**: 12分 (目標: 15分以内)

### パフォーマンス最適化
- **並列実行**: 3OS × 5Python = 15並列
- **キャッシュ**: pip, pre-commit
- **早期失敗**: 最初のエラーで停止

## 🔒 セキュリティ

### 自動スキャン
- **依存関係**: safety, pip-audit
- **コード解析**: bandit, semgrep
- **シークレット**: trufflehog

### 実行タイミング
- **週次**: 毎週月曜日 8:00 UTC
- **手動**: Actions → Security → Run workflow
- **PR時**: requirements 変更時

## 📦 リリース

### 自動リリース
```bash
# バージョン更新
# pyproject.toml version: "1.2.3"

# タグ作成・プッシュ
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3

# → 自動で GitHub Release 作成
```

### リリース内容
- **パッケージ**: wheel, tar.gz
- **リリースノート**: 自動生成
- **アーティファクト**: GitHub Releases に添付

## 🚨 トラブルシューティング

### よくある CI エラー

#### flake8 エラー
```bash
# エラー例: E501 line too long
# 修正方法
black src tests  # 自動修正
```

#### テスト失敗
```bash
# ローカルで詳細確認
pytest tests/test_specific.py -v --tb=long
```

#### カバレッジ不足
```bash
# カバレッジレポート確認
pytest --cov=src --cov-report=html
# htmlcov/index.html を開く
```

### パフォーマンス問題
```bash
# 遅いテスト特定
pytest --durations=10

# 並列実行
pytest -n auto
```

## 📚 詳細ドキュメント

- **運用マニュアル**: [`doc/operations/CICD_OPERATIONS_MANUAL.md`](operations/CICD_OPERATIONS_MANUAL.md)
- **開発者ガイド**: [`doc/DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md)
- **設計文書**: [`doc/design/CICD_ARCHITECTURE_DESIGN.md`](design/CICD_ARCHITECTURE_DESIGN.md)

## 🤝 サポート

### 問題報告
- **GitHub Issues**: バグ報告・機能要求
- **GitHub Discussions**: 質問・議論

### 緊急時
- **CI 無効化**: Settings → Actions → Disable
- **ホットフィックス**: hotfix/ ブランチから緊急修正

---

**最終更新**: 2025-07-14
# PGSD User Manual

PostgreSQL Schema Diff Tool (PGSD) 完全ユーザーマニュアル

## 📖 目次

### 🚀 Getting Started - はじめに
- [インストール手順](getting_started/installation.md) - PGSDのインストール方法
- [初回スキーマ比較](getting_started/first_comparison.md) - 最初のスキーマ比較実行
- [基本ワークフロー](getting_started/basic_workflow.md) - 日常的な使用フロー

### ⚙️ Configuration - 設定
- [設定ファイル](configuration/config_file.md) - YAML設定ファイルの書き方
- [データベース設定](configuration/database_setup.md) - データベース接続の設定
- [出力設定](configuration/output_settings.md) - レポート出力の詳細設定

### 🔧 Features - 機能詳細
- [スキーマ比較機能](features/schema_comparison.md) - 比較機能の詳細解説
- [レポート形式](features/report_formats.md) - HTML、Markdown、JSON、XML形式
- [差分解析](features/diff_analysis.md) - 差分検出の仕組み
- [自動化機能](features/automation.md) - スクリプトとCI/CD連携

### 🎯 Advanced - 高度な使用法
- [パフォーマンス調整](advanced/performance_tuning.md) - 大規模スキーマの最適化
- [カスタムテンプレート](advanced/custom_templates.md) - レポートテンプレートのカスタマイズ
- [CI/CD統合](advanced/ci_cd_integration.md) - 継続的インテグレーション
- [スクリプト活用](advanced/scripting.md) - 自動化スクリプトの作成

### 🔧 Troubleshooting - トラブルシューティング
- [よくある問題](troubleshooting/common_issues.md) - 頻出問題と解決法
- [エラーメッセージ](troubleshooting/error_messages.md) - エラーメッセージの意味と対処
- [パフォーマンス問題](troubleshooting/performance_issues.md) - 性能問題の解決

### 📚 Reference - リファレンス
- [CLIコマンド](reference/cli_commands.md) - 全コマンドの詳細仕様
- [設定リファレンス](reference/config_reference.md) - 設定項目の完全リスト
- [APIリファレンス](reference/api_reference.md) - プログラマティック使用法

---

## 🎯 クイックスタート

### 1. インストール
```bash
pip install pgsd
```

### 2. 基本的なスキーマ比較
```bash
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

### 3. HTMLレポート確認
生成されたHTMLレポートをブラウザで確認：
```bash
open ./reports/schema_diff_*.html
```

---

## 📋 マニュアルの使い方

### 初心者の方
1. **[インストール手順](getting_started/installation.md)** から始める
2. **[初回スキーマ比較](getting_started/first_comparison.md)** で実際に試す
3. **[基本ワークフロー](getting_started/basic_workflow.md)** で日常使用を学ぶ

### 既存ユーザーの方
- **[機能詳細](features/)** で新機能を確認
- **[高度な使用法](advanced/)** で効率化を図る
- **[トラブルシューティング](troubleshooting/)** で問題解決

### 開発者・運用者の方
- **[CI/CD統合](advanced/ci_cd_integration.md)** で自動化を実現
- **[スクリプト活用](advanced/scripting.md)** でカスタマイズ
- **[APIリファレンス](reference/api_reference.md)** でプログラム連携

---

## 🆘 サポート

### ヘルプの取得
```bash
pgsd --help
pgsd compare --help
```

### コミュニティ・サポート
- **GitHub Issues**: [問題報告・機能要望](https://github.com/omasaaki/pgsd/issues)
- **GitHub Discussions**: [質問・議論](https://github.com/omasaaki/pgsd/discussions)
- **Documentation**: [オンラインドキュメント](https://github.com/omasaaki/pgsd/docs)

### 緊急時の対応
1. **[よくある問題](troubleshooting/common_issues.md)** をチェック
2. **[エラーメッセージ](troubleshooting/error_messages.md)** で詳細確認
3. GitHubでIssue作成（エラーログ添付）

---

## 📝 貢献・フィードバック

PGSDの改善にご協力ください：

- **バグ報告**: [GitHub Issues](https://github.com/omasaaki/pgsd/issues/new/choose)
- **機能要望**: [Feature Request](https://github.com/omasaaki/pgsd/issues/new?template=feature_request.md)
- **ドキュメント改善**: [Documentation PR](https://github.com/omasaaki/pgsd/pulls)
- **コード貢献**: [Development Guide](../DEVELOPER_GUIDE.md)

---

## 📄 ライセンス

PGSD is licensed under the MIT License. See [LICENSE](../../LICENSE) for details.

Copyright (c) 2025 PGSD Development Team
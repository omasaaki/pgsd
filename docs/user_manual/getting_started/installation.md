# インストール手順

PGSDのインストール方法について説明します。

## 📋 システム要件

### 必須要件
- **Python**: 3.9以上
- **オペレーティングシステム**: Linux、macOS、Windows
- **メモリ**: 最低512MB、推奨1GB以上
- **ディスク容量**: 100MB以上の空き容量

### データベース要件
- **PostgreSQL**: 13.x、14.x、15.x、16.x
- **ネットワークアクセス**: 比較対象データベースへの接続権限
- **データベース権限**: スキーマの読み取り権限（SELECT、USAGE）

## 🚀 インストール方法

### 方法1: pip経由でのインストール（推奨）

最も簡単で推奨される方法です：

```bash
# 最新版をインストール
pip install pgsd

# 特定バージョンをインストール
pip install pgsd==1.0.0

# 開発版をインストール
pip install --pre pgsd
```

#### インストール確認
```bash
pgsd version
```

### 方法2: 仮想環境でのインストール

本番環境や複数プロジェクトでの使用時に推奨：

#### venv使用（Python標準）
```bash
# 仮想環境作成
python -m venv pgsd-env

# 仮想環境アクティベート
source pgsd-env/bin/activate  # Linux/macOS
# pgsd-env\Scripts\activate.bat  # Windows

# PGSDインストール
pip install pgsd
```

#### pyenv使用（推奨）
```bash
# Python環境作成
pyenv install 3.11.7
pyenv virtualenv 3.11.7 pgsd-env
pyenv activate pgsd-env

# PGSDインストール
pip install pgsd
```

### 方法3: ソースからのインストール

開発者や最新機能が必要な場合：

```bash
# ソースコード取得
git clone https://github.com/omasaaki/pgsd.git
cd pgsd

# 開発モードでインストール
pip install -e .

# または通常インストール
pip install .
```

### 方法4: Docker使用

環境を分離したい場合：

```bash
# PGSDコンテナを使用
docker run --rm -v $(pwd):/workspace pgsd/pgsd:latest \
  compare --source-host host.docker.internal --source-db db1 \
          --target-host host.docker.internal --target-db db2
```

## 🔧 オプション依存関係

### 開発者向け依存関係
```bash
# 開発・テスト環境のセットアップ
pip install pgsd[dev]

# または個別インストール
pip install pgsd pytest black mypy flake8
```

### 特定機能の依存関係
```bash
# パフォーマンス向上
pip install pgsd[performance]

# エクスポート機能拡張
pip install pgsd[export]
```

## 🖥️ OS別セットアップ

### Linux (Ubuntu/Debian)
```bash
# システム依存関係
sudo apt-get update
sudo apt-get install python3-pip python3-venv postgresql-client

# PGSD インストール
pip3 install pgsd
```

### Linux (CentOS/RHEL)
```bash
# システム依存関係
sudo yum install python3-pip postgresql

# PGSD インストール
pip3 install pgsd
```

### macOS
```bash
# Homebrewでの依存関係インストール
brew install python postgresql

# PGSD インストール
pip3 install pgsd
```

### Windows
```powershell
# Python インストール（python.orgから）
# PostgreSQL クライアントインストール

# PGSD インストール
pip install pgsd
```

## ✅ インストール確認

### 基本動作確認
```bash
# バージョン確認
pgsd version

# ヘルプ表示
pgsd --help

# コマンド一覧
pgsd --help
```

### 詳細確認
```bash
# システム情報表示
pgsd version --verbose

# 依存関係確認
pip show pgsd
```

## 🔄 アップデート

### 最新版への更新
```bash
# pip経由でのアップデート
pip install --upgrade pgsd

# 特定バージョンへの更新
pip install --upgrade pgsd==1.1.0
```

### 開発版への更新
```bash
# ソースからの更新
cd pgsd
git pull origin main
pip install -e .
```

## 🗑️ アンインストール

### 通常のアンインストール
```bash
pip uninstall pgsd
```

### 完全なクリーンアップ
```bash
# PGSD関連ファイル削除
pip uninstall pgsd
rm -rf ~/.pgsd/  # 設定ディレクトリ
rm -rf ~/pgsd-reports/  # レポートディレクトリ
```

## 🐛 インストール時のトラブルシューティング

### よくある問題

#### 1. Python バージョンエラー
```
ERROR: Python 3.8 is not supported
```
**解決策**: Python 3.9以上をインストール

#### 2. 権限エラー
```
ERROR: Permission denied
```
**解決策**: 
```bash
# ユーザー環境にインストール
pip install --user pgsd

# または仮想環境使用
python -m venv pgsd-env
source pgsd-env/bin/activate
pip install pgsd
```

#### 3. ネットワークエラー
```
ERROR: Could not find a version that satisfies the requirement pgsd
```
**解決策**:
```bash
# インデックスURLの指定
pip install -i https://pypi.org/simple/ pgsd

# キャッシュクリア
pip cache purge
pip install pgsd
```

#### 4. 依存関係コンフリクト
```
ERROR: pip's dependency resolver does not currently take into account...
```
**解決策**:
```bash
# 仮想環境での隔離インストール
python -m venv clean-env
source clean-env/bin/activate
pip install pgsd
```

### ログ確認方法
```bash
# 詳細インストールログ
pip install --verbose pgsd

# pip ログ確認
pip list
pip show pgsd
```

## 🚀 次のステップ

インストールが完了したら：

1. **[初回スキーマ比較](first_comparison.md)** - 実際にPGSDを使ってみる
2. **[基本ワークフロー](basic_workflow.md)** - 日常的な使用方法を学ぶ
3. **[設定ファイル](../configuration/config_file.md)** - 効率的な設定方法

## 📞 サポート

インストールに関する問題：
- [トラブルシューティング](../troubleshooting/common_issues.md)
- [GitHub Issues](https://github.com/omasaaki/pgsd/issues)
- [よくある質問](../troubleshooting/common_issues.md#installation-issues)
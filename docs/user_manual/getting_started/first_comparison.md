# 初回スキーマ比較

PGSDを使って初めてスキーマ比較を実行する手順を説明します。

## 🎯 この章で学ぶこと

- PGSDの基本的な使用方法
- 最初のスキーマ比較実行
- レポートの見方
- 基本的なトラブルシューティング

## 📋 事前準備

### 必要な情報
以下の情報を用意してください：

- **ソースデータベース**（比較元）
  - ホスト名/IPアドレス
  - ポート番号（通常5432）
  - データベース名
  - ユーザー名/パスワード
  - スキーマ名（通常は`public`）

- **ターゲットデータベース**（比較先）
  - 上記と同様の情報

### データベース権限確認
比較を実行するユーザーに以下の権限があることを確認：

```sql
-- スキーマへのアクセス権限
GRANT USAGE ON SCHEMA public TO your_user;

-- テーブルへの読み取り権限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;

-- シーケンスへの読み取り権限  
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

## 🚀 初回実行

### ステップ1: 最も簡単な比較

同一サーバー上の2つのデータベースを比較：

```bash
pgsd compare \
  --source-host localhost \
  --source-db development \
  --target-host localhost \
  --target-db staging
```

### ステップ2: リモートデータベースとの比較

```bash
pgsd compare \
  --source-host prod.company.com \
  --source-db production \
  --source-user app_reader \
  --source-password your_password \
  --target-host localhost \
  --target-db local_copy
```

### ステップ3: 出力先の指定

```bash
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --output ./my-reports \
  --format html
```

## 📊 実行例とその解説

### 例1: 開発環境と本番環境の比較

```bash
# 実行コマンド
pgsd compare \
  --source-host prod.example.com \
  --source-db myapp_production \
  --source-user readonly_user \
  --target-host dev.example.com \
  --target-db myapp_development \
  --target-user dev_user \
  --schema public \
  --format html \
  --output ./comparison-reports

# 実行中の出力例
🔍 Connecting to source database...
✅ Source connection established
🔍 Connecting to target database...  
✅ Target connection established
📊 Analyzing schema 'public'...
📋 Found 15 tables, 8 views, 12 indexes
🔍 Detecting differences...
📄 Generating HTML report...
✅ Comparison completed successfully!
📁 Report saved: ./comparison-reports/schema_diff_20250715_143022.html
```

### 例2: 出力内容の理解

実行が成功すると、以下のようなファイルが生成されます：

```
comparison-reports/
├── schema_diff_20250715_143022.html    # メインレポート
└── assets/                             # 関連ファイル（CSS等）
    ├── styles.css
    └── scripts.js
```

## 📋 レポートの確認

### HTMLレポートを開く

```bash
# ブラウザでレポートを開く
open ./comparison-reports/schema_diff_*.html

# または
# Windows: start ./comparison-reports/schema_diff_*.html
# Linux: xdg-open ./comparison-reports/schema_diff_*.html
```

### レポートの構成

HTMLレポートには以下のセクションが含まれます：

1. **サマリー**: 差分の概要
2. **テーブル比較**: テーブル構造の差分
3. **インデックス比較**: インデックスの差分
4. **制約比較**: 制約（外部キー、CHECK等）の差分
5. **詳細差分**: 各項目の詳細情報

### レポートの読み方

```html
<!-- サマリー例 -->
📊 Summary
- Tables: 12 identical, 3 modified, 1 added, 0 removed
- Columns: 45 identical, 5 modified, 2 added, 1 removed
- Indexes: 8 identical, 2 modified, 1 added, 0 removed
```

**色分けの意味**:
- 🟢 **緑**: 一致（問題なし）
- 🟡 **黄**: 変更あり（要確認）
- 🔴 **赤**: 追加/削除（要注意）

## 🔧 よく使用されるオプション

### 認証情報の指定

```bash
# パスワードを環境変数で指定
export PGPASSWORD="your_password"
pgsd compare --source-host localhost --source-db db1 \
             --target-host localhost --target-db db2

# .pgpassファイルを使用
echo "localhost:5432:*:username:password" >> ~/.pgpass
chmod 600 ~/.pgpass
```

### 特定のスキーマのみ比較

```bash
# アプリケーション固有のスキーマを比較
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --schema app_data
```

### 複数形式での出力

```bash
# HTML とMarkdown の両方を生成
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format html
  
pgsd compare \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2 \
  --format markdown
```

## 🐛 初回実行時のトラブルシューティング

### よくあるエラーと解決法

#### 1. 接続エラー
```
Error: could not connect to server: Connection refused
```

**確認事項**:
- ホスト名/IPアドレスが正しいか
- ポート番号が正しいか（デフォルト5432）
- PostgreSQLサービスが起動しているか
- ファイアウォールでポートが開いているか

**解決例**:
```bash
# 接続テスト
telnet your-db-host 5432

# PostgreSQL接続テスト
psql -h your-db-host -p 5432 -U your-user -d your-db
```

#### 2. 認証エラー
```
Error: FATAL: password authentication failed for user "app_user"
```

**解決例**:
```bash
# 正しい認証情報で再実行
pgsd compare \
  --source-host localhost \
  --source-db mydb \
  --source-user correct_username \
  --source-password correct_password \
  --target-host localhost \
  --target-db mydb2
```

#### 3. 権限エラー
```
Error: permission denied for schema public
```

**解決例**:
```sql
-- データベース管理者として実行
GRANT USAGE ON SCHEMA public TO your_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;
```

#### 4. スキーマが見つからない
```
Error: schema "app_schema" does not exist
```

**確認方法**:
```bash
# 利用可能なスキーマを一覧表示
pgsd list-schemas --host localhost --db mydb --user myuser
```

### デバッグモード

詳細な情報が必要な場合：

```bash
# 詳細ログを有効化
pgsd compare --verbose \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2

# エラーのみ表示
pgsd compare --quiet \
  --source-host localhost --source-db db1 \
  --target-host localhost --target-db db2
```

## ✅ 成功の確認

初回実行が成功した場合：

1. **終了コード0**で完了
2. **HTMLレポートが生成**される
3. **エラーメッセージが出力されない**
4. **レポートがブラウザで正常表示**される

### 次のステップの確認

```bash
# 生成されたファイルを確認
ls -la ./reports/

# レポートサイズの確認（正常に生成されている場合は数KB以上）
du -h ./reports/schema_diff_*.html

# レポートの内容をざっと確認
head -20 ./reports/schema_diff_*.html
```

## 🎓 学習ポイント

初回実行で理解しておくべき重要なポイント：

### 1. コマンド構造の理解
```bash
pgsd [グローバルオプション] compare [比較オプション]
```

### 2. 必須パラメータ
- `--source-host` と `--source-db`
- `--target-host` と `--target-db`

### 3. よく使用するオプション
- `--schema`: 比較するスキーマの指定
- `--output`: レポート出力先
- `--format`: レポート形式

### 4. 認証方法
- コマンドライン引数
- 環境変数
- .pgpassファイル

## 🚀 次のステップ

初回比較が成功したら：

1. **[基本ワークフロー](basic_workflow.md)** - 日常的な使用パターンを学ぶ
2. **[設定ファイル](../configuration/config_file.md)** - 効率的な設定管理
3. **[レポート形式](../features/report_formats.md)** - 様々な出力形式の活用

## 💡 ヒント

- **小さなデータベースから始める**: 初回は小規模なデータベースで試す
- **接続をテストしてから**: psqlでの接続確認を先に行う
- **権限を事前確認**: データベース管理者と権限を確認
- **レポートを確認**: 生成されたレポートの内容を必ず確認
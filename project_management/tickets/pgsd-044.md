# PGSD-044: HTMLレポートに詳細な変更内容を表示する機能の実装

## 📋 基本情報

- **チケット番号**: PGSD-044
- **タイトル**: HTMLレポートに詳細な変更内容を表示する機能の実装
- **種別**: 機能改善 (Feature Enhancement)
- **優先度**: High
- **作成日**: 2025-07-19
- **担当者**: システム開発チーム
- **推定工数**: 2時間
- **ステータス**: DONE

## 🎯 概要

### 現在の状況
現在のHTMLレポートはサマリー情報のみを表示しており、以下の詳細情報が表示されていません：
- 追加・削除・変更されたテーブルの具体的な名前とその詳細
- 各テーブルのカラム変更の詳細（カラム名、データ型、制約等）
- インデックスや制約の変更内容

### 原因
`src/pgsd/reports/html.py`の96行目で、シンプルテンプレート（`SIMPLE_HTML_TEMPLATE`）を使用しているため、詳細情報が表示されていない。

### 期待される動作
HTMLレポートに以下の詳細情報を表示：
1. **テーブル変更の詳細**
   - 追加されたテーブル: テーブル名、カラム定義、制約
   - 削除されたテーブル: テーブル名
   - 変更されたテーブル: テーブル名と変更内容

2. **カラム変更の詳細**
   - 追加・削除されたカラム: テーブル名、カラム名、データ型
   - 変更されたカラム: 変更前後の定義

3. **その他の変更**
   - インデックスの追加・削除・変更
   - 制約の追加・削除・変更

## 🔧 実装方針

### 1. テンプレート切り替え
- `SIMPLE_HTML_TEMPLATE`から完全な`HTML_TEMPLATE`への切り替え
- Jinja2テンプレートエラーの解決確認

### 2. テンプレート修正
- 必要に応じて`templates.py`のHTML_TEMPLATEを修正
- グループ化された変更内容の適切な表示

### 3. コンテキストデータ確認
- `_prepare_template_context`メソッドで必要なデータが渡されているか確認
- `GroupedDiffResult`の活用

## 📝 実装タスク

- [ ] `html.py`でHTML_TEMPLATEを使用するよう修正
- [ ] HTML_TEMPLATEのJinja2構文エラーを修正（必要な場合）
- [ ] 詳細情報が正しく表示されることを確認
- [ ] テストケースの更新

## 🧪 テスト計画

### 1. 機能テスト
- スキーマ比較結果の詳細が表示されること
- 各種変更（テーブル、カラム、制約等）が正しく表示されること
- HTMLレポートが正常に生成されること

### 2. 回帰テスト
- 既存の機能に影響がないこと
- エラーなくレポートが生成されること

## 🎯 受入条件

1. **詳細表示**
   - テーブルの追加・削除・変更が具体的に表示される
   - カラムの変更内容が詳細に表示される
   - 変更内容が階層的に整理されて表示される

2. **ユーザビリティ**
   - 検索・フィルター機能が動作する（実装済みの場合）
   - レスポンシブデザインが維持される
   - 視覚的に分かりやすい表示

3. **品質**
   - Jinja2テンプレートエラーが発生しない
   - パフォーマンスが劣化しない
   - テストが通る

## 📚 関連情報

### 影響を受けるファイル
- `src/pgsd/reports/html.py`: HTMLレポート生成クラス
- `src/pgsd/reports/templates.py`: HTMLテンプレート定義
- `tests/unit/reports/test_html.py`: HTMLレポートのテスト

### 関連チケット
- PGSD-041: HTMLレポート生成のJinja2テンプレートエラー修正（完了）
- PGSD-034: リポート出力方法の改善 - テーブルごとのグルーピング（完了）
- PGSD-035: 先進的なレポートデザインとレイアウトの実装（完了）

### 技術的詳細
```python
# 現在の実装（96行目）
template_content = SIMPLE_HTML_TEMPLATE

# 修正後
template_content = HTML_TEMPLATE
```

## 📝 作業記録

- **開始日時**: 2025-07-19
- **完了日時**: 2025-07-19
- **実績時間**: 1時間
- **見積との差異**: -1時間（効率化により短縮）

## 🔄 進捗ステップ

### Step 1: 分析と修正（30分）
- [ ] 現在の実装状況の確認
- [ ] HTML_TEMPLATEの構造確認
- [ ] テンプレート切り替えの実装

### Step 2: テンプレート調整（1時間）
- [ ] Jinja2構文エラーの修正
- [ ] 詳細表示部分の実装確認
- [ ] スタイルとレイアウトの調整

### Step 3: テストと検証（30分）
- [ ] 実データでのテスト実行
- [ ] 詳細表示の確認
- [ ] テストケースの更新

---
**チケット作成者**: Claude Assistant  
**最終更新**: 2025-07-19
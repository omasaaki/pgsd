# dev_rule.md - 開発ルール

## 📋 概要
このドキュメントは、コードの実装を伴う開発プロセスにおける最優先のルールを定義します

## 参照ドキュメント
- 基本ルール: project_management_rule.md
- チケット駆動プロセス: tid.md
- 作業ルール: work_rule.md

## 📋 開発ルール

```
- コードは既存のコード規約に従う
- コードのコメントは英語で書く
- エラーハンドリングを適切に実装する
- パフォーマンスとセキュリティを考慮する
- テストカバレッジ80%以上を目指す
```

## トラッカー定義

開発プロジェクトではチケットのトラッカーを以下のもので置き換える
1. **機能**: 機能チケット
2. **要望**: 要望チケット
3. **バグ**: バグチケット

## 実行可否確認基準

```
以下の場合は必ず実行可否確認を行う：
1. **設計変更**: アーキテクチャや他機能への影響がある場合
2. **技術選定**: 新しいライブラリ・フレームワーク・ツールの導入
3. **データベース変更**: スキーマ変更やデータ移行を伴う作業
4. **API変更**: 既存APIの変更や削除（破壊的変更）
5. **セキュリティ影響**: 認証・認可・暗号化に関わる変更
6. **パフォーマンス影響**: システム性能に大きな影響を与える可能性がある変更
7. **大規模実装**: 見積もりが4時間を超える実装作業
8. **外部連携**: 他システムとの連携に関わる変更
```

## 開発フロー

### チケット着手時
```
チケット[ID]の作業を開始します
1. ステータスを「IN_PROGRESS」に更新
2. 開始時刻を記録
3. 依存チケットの完了状態を確認
4. 作業内容を理解し、計画を立てる
5. 実行してもよいかをy/nで確認する
6. 設計作業を開始
7. テストコードの実装作業を開始
8. 実装作業を開始
9. テストコード実施
10. テストでエラーが発生した場合：
   a. エラー内容を分析
   b. 設計の見直しが必要か判断
   c. 必要に応じて4.に戻る
   d. 軽微な修正の場合は6.に戻る
11. 最終確認を実施
```

#### 設計作業時
```
チケット[ID]の設計作業を開始します
1. アーキテクチャ設計が必要であればアーキテクチャ設計作業を開始してもよいかをy/nで確認する
2. アーキテクチャ設計が必要であればアーキテクチャ設計を開始
3. 詳細設計作業を開始してもよいかをy/nで確認する
4. 詳細設計を開始
5. テストコード作成作業を開始してもよいかをy/nで確認する
6. テストコード作成を開始
7. 実装作業を開始してもよいかをy/nで確認する
```

##### アーキテクチャ設計時
```
[チケットID]のアーキテクチャ設計を行います。
1. アーキテクチャ設計を開始
- 影響範囲の分析
- 既存コードとの整合性確認
- データモデル設計
- API設計
- UI/UX設計
- セキュリティ考慮事項
2. アーキテクチャ設計の設計ドキュメントを作成/更新
```

##### 詳細設計時
```
[チケットID]の詳細設計を行います。
1. 詳細設計を開始
- 影響範囲の分析
- 既存コードとの整合性確認
2. 詳細設計の設計ドキュメントを作成/更新
```

##### テストコード作成時
```
[チケットID]のテストコードを作成します。
1. テストコード設計を開始
- 単体テスト設計
- 結合テスト設計
- E2Eテスト設計
- テストデータ準備
- モック設計
2. テストコード実装作業を開始
3. テストの設計ドキュメントを作成/更新
```

#### 実装作業時
```
チケット[ID]の実装作業を開始します
1. コード実装作業を開始してもよいかをy/nで確認する
2. コード実装作業を開始する
3. 品質チェック作業を開始してもよいかをy/nで確認する
4. 品質チェック作業を開始する
```
##### コード実装時
```
[チケットID]の実装を行います。
- 既存のコード規約に従う
- エラーハンドリングの実装
- パフォーマンスの考慮
- セキュリティの考慮
```

##### 品質チェック時
```
[チケットID]の品質チェックを実行します。
1. セルフレビューを実施
2. 可能であれば静的解析チェックを実施
```

###### セルフレビュー時
```
[チケットID]のセルフレビューを実施します。
1. 要件との整合性を確認
2. 設計との整合性を確認
3. コード品質を確認
4. テストカバレッジを確認
5. エラーハンドリングを確認
6. パフォーマンスを考慮しているかを確認
7. セキュリティを考慮しているかを確認
8. 受入条件の達成確認
9. ドキュメントの完成度確認
```

###### 静的解析時
```
[チケットID]の静的解析を実施します。
1. 静的解析を実施
2. 静的解析結果を報告
```

#### テストコード実施
```
[チケットID]のテストコードを実行します。
- テスト実行と結果確認
- テストカバレッジの確認
1. テストコードを実行
2. テスト結果を確認
3. テストカバレッジを確認
4. テスト結果を報告
```

#### 最終確認
```
[チケットID]の最終確認を行います。
1. 最終確認を実施
- 全ての受入条件が満たされているか
- 関連するドキュメントが更新されているか
- テストが全て通るか
- 本番環境での動作に問題がないか
```

## ドキュメント管理

### 設計ドキュメントのディレクトリ構造
```
  {プロジェクトルート}/
  ├── doc/
  │   ├── DESIGN_XXX.md                    # 設計ドキュメント
  │   ├── DESIGN_YYY.md                    # 設計ドキュメント
  │   ├── DESIGN_ZZZ.md                    # 設計ドキュメント
  │   ├── uml/                         # PlantUMLソースファイル
  │   │   ├── architecture.puml        # アーキテクチャ図
  │   │   ├── sequence.puml            # シーケンス図
  │   │   ├── ...
  │   │   └── activity.puml            # アクティビティ図
  │   └── images/                      # PNG出力ファイル
  │       ├── architecture.png
  │       ├── sequence.png
  │       ├── ...
  │       └── activity.png
```

## 判断基準

### 設計変更の判断
1. 影響範囲が限定的 → 軽微な変更として対応
2. 他の機能に影響 → 設計の見直しが必要
3. アーキテクチャに影響 → 別チケットで対応検討

### エスカレーション基準
1. 見積もりの2倍以上の時間がかかる
2. 設計の根本的な見直しが必要
3. 他チームとの調整が必要
4. セキュリティ上の懸念がある

## コード品質ガイドライン

### コーディング規約
```
コードを実装する際の規約：
1. 既存コードのスタイルを維持する
2. 変数名は意味が明確になるように命名する
3. 関数は単一責任の原則に従う
4. コメントは必要最小限にとどめる
5. マジックナンバーを避ける
```

### エラーハンドリング
```
エラー処理の基本方針：
1. 予期されるエラーは適切にキャッチする
2. エラーメッセージはユーザーにわかりやすく
3. ログを適切に記録する
4. リトライ機構を実装する（必要に応じて）
```

### セキュリティ
```
セキュリティ対策：
1. 入力値の検証を徹底する
2. SQLインジェクション対策を実施
3. XSS対策を実施
4. 機密情報をハードコードしない
5. 適切な認証・認可を実装
```

### テスト方針
```
テストの基本方針：
1. テストファーストで開発する
2. 単体テストを必ず作成する
3. 結合テストを適切に実施
4. カバレッジ80%以上を維持
5. テストは保守しやすく書く
```

## 注意事項

1. **参照ドキュメント**: project_management_rule.md（プロジェクト管理ルール）、tid.md（チケット駆動プロセスルール）
2. **確認の重要性**: 重要な決定は必ず確認を取る
3. **ドキュメント**: 作業に関する文書を常に最新に保つ
4. **コミュニケーション**: 技術的な判断の根拠を明確に説明

## 更新履歴
- **2025-07-09**: 新規作成

# 調査の分類・仕様とTestsの対応

## Confirmed

コード調査で確認した構造・現在の動作をARCHITECTURE、BUSINESS_RULES、DATABASE、RELEASEに記録した。実運用・業務承認の確認とは区別する。

既存資料との不一致は下記に保持する。今回、既存資料の本文・アプリ動作を修正していない。

| 資料 | 不一致・位置づけ | 照合先 |
| --- | --- | --- |
| README.md、docs/postgresql-migration.md | 通常運用の接続先を4DBと説明する箇所があるが、現在の実装は3接続先 | infrastructure/postgres/defect_repository.py |
| database/postgresql/migration_notes.md | 検査員参照元にnumeric_inspection_recordsを含む | 現行Repository・README・test_postgres_repository_sql.pyはQR履歴 |
| docs/business_app_architecture.md | PySide6・presentation構成の設計例と、現在のpywebview構成の差 | webview/app.py |
| docs/migration_map.md | PostgreSQLを将来の差替え先と記載 | 現行Repository・運用資料は移行済み |
| DESIGN/DESIGN.mdとdocs/DESIGN.md | 配色・サイドバー等の方針差。前者には別アプリ名もある | READMEはdocs/DESIGN.mdを主参照と指定 |

設定例のpostgresとコード既定accessは別概念で、直接の矛盾ではない。既存Testsと現在の実装に直接の矛盾は調査で確認されなかったが、未網羅の動作は残る。

## Assumption

- 旧移行資産・Access資料は過去の経緯と切り戻しのために保存されている可能性がある。削除・通常利用の判断根拠にはしない。
- DB境界と帳票確認が今後も繰り返されると見込みDomain Skillを設けたが、実際の頻度は未確認。不要なら後の具体的な改善案として統合を検討する。

## Unknown / Human Validation Required

- 切粉除外、Pロット、工程03の業務的な理由。集計出力のP条件・切粉差引き・金額正の条件の維持はユーザーが明示した。
- 単重・単価の単位、丸め、欠損・負数・重複マスターの扱い。
- QR履歴の最新検査員と旧Access履歴の結果差を許容するか。
- 現行本番スキーマ・制約・権限・データ品質、バックアップと復旧方法。
- 移行資産の現在の利用可否、専用実行環境、同時更新・途中停止・再実行の保証。
- 配布経路、認証情報同梱の扱い、バージョン、リリース承認・ロールバック運用。
- 保存失敗時の部分ファイル、Excelで開いた保存先への書込み、実UIの上書き確認。

2026-10-12の実装で集計出力の検査日・重複採用・丸め方を確定した。仕様はBUSINESS_RULESを参照。元の重複記録が訂正か別作業分かの業務上の意味を確定したわけではない。Access切り戻し時の外観検査DB到達性と実ODBC確認は残る。

## 重要動作とTests

| 仕様・動作 | 自動Test | 残る確認 |
| --- | --- | --- |
| 設定・backend選択 | test_config.py | PG時のAccess設定必須、全探索順・互換キー・環境汚染の網羅は不足 |
| 日英列・ドメイン変換 | test_domain_mappers.py | 異常型・境界値の全組合せは未網羅 |
| PG品番検索・最新QR検査員SQL | test_postgres_repository_sql.py | 実DBでのSQL実行・欠損・大量データ |
| Access参照テーブル | test_access_repository_sql.py | 実ODBC・JOIN増幅・切り戻し同等性 |
| 検索・表示集計 | test_defect_service.py、test_report_business_rules.py | 実画面・汚れた号機値 |
| 集計の切粉除外・P条件・金額条件 | test_report_business_rules.py | 単位・丸め・本番データ整合性 |
| 廃棄のQR対象ロット・金額条件の違い | test_report_business_rules.py | 実DBの工程・日付条件 |
| Excel読戻し・集計書式・再保存 | test_export_service.py | UI取消・上書き、ロック・途中停止・大規模出力 |
| 日付入力・Bridgeエラー | 未整備 | 自動化可能。実画面も必要 |
| 移行・復旧・再実行 | 未整備 | 隔離DB・匿名データと運用確認が必要 |
| exe・短い画面での操作 | 自動化なし | 対象Windows環境で手動確認 |

追加Testsは現在の動作を検証し、未確定仕様を新たに定めない。

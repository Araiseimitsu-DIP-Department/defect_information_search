---
name: database-operations
description: 不具合情報検索のDB切替・SQL・日英列対応・データ移行を調査または変更するときに使う。
---

# DB境界の確認

仕様は docs/DATABASE.md、詳細列対応は docs/postgresql-migration.md、不一致は docs/KNOWN_GAPS.md。

1. 通常アプリの参照、Access切り戻し、旧単一DB移行、DB別移行、製品マスター再作成のどれかを特定する。接続設定の探索先と対象DBを確認し、実値は出力しない。
2. SQLの列別名→Mapper→ドメイン→表示・出力を追う。切替では日付条件、検査員補完、列数、欠損、JOINの行数差を確認する。SQLテスト成功を実DB検証済みとみなさない。
3. 更新時は [共通検証](../development-workflow/references/data-update-verification.md) を適用し、対象・件数・一意性・commit境界・バックアップ・再実行条件を整理する。名前だけでdry-runや無害と判断せず実装を読む。
4. 書込み前の検査を先に用意する。既存テーブル検出や件数一致は重複・内容一致・再実行安全性の証明にならない。docs配下の実行スクリプトの副作用と専用依存を確認する。
5. Testsは tests/test_config.py、test_access_repository_sql.py、test_postgres_repository_sql.py、test_domain_mappers.pyから影響範囲を選ぶ。実DBスモークは接続対象と依頼範囲を確認後に使う。

本SkillはDB境界・移行を担当する。廃棄計算・Excelは [report-output](../report-output/SKILL.md)、通常の実装手順は対応する開発Skillを使う。

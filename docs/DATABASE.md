# DB・設定・更新境界

コード調査によるConfirmed。接続実値・本番データ・DB権限は含めない。

## 通常アプリの参照

| 用途 | 接続先の役割 | テーブル |
| --- | --- | --- |
| 不具合 | 外観検査DB | defect_information |
| 検査員名 | 外観検査DB | numeric_inspector_master |
| QR履歴・廃棄対象ロット | 現品票DB | qr_history |
| 品番候補 | 現品票DB | delivery_label_history |
| 製品属性・単価・単重 | ARAIマスターDB | product_master |
| 集計出力の検査日 | 外観検査DB | appearance_inspection_summaries、appearance_inspection_summary_archives |

現行のコードは3接続先を使い、DB間のJOINをPythonで行う。詳細列対応は [postgresql-migration](postgresql-migration.md) に集約する。

PGの検査員補完はロットをtrimし、process_nameに数値検査を含みpositionが空でない履歴からdate_time DESC NULLS LAST、id DESCの最新1件を選び、positionを検査員IDとして名前と照合する。numeric_inspection_recordsは使わない。Accessはt_数値検査記録をロットでLEFT JOINし、検査員マスターと結合するため履歴数による行増加の可能性がある。

通常RepositoryはSELECTのみ。PGは検索ごとにpsycopg接続、30秒の接続タイムアウトとIdentifierで引用したsearch_path設定を行う。DB権限やトランザクションのread-only強制は未確認。Access接続文字列にはReadOnly=1がある。IN条件はPGで500件、Accessで200件に分割する。複数DB・複数検索全体で一つの整合したスナップショットは保証されない。

## アプリ設定

| 環境変数 | 役割・現在の読込動作 |
| --- | --- |
| ACCESS_DB_PATH | Access運用時のみ必須。PG起動時にAccessへの接続・専用モジュール読込みはしない |
| ACCESS_APPEARANCE_DB_PATH | Accessの集計出力専用の外観検査DBパス。未設定時はACCESS_DB_PATHを使う。通常・保存の集計テーブルがない場合はエラーで停止し、指示日へ代用しない |
| DB_BACKEND | access / postgres。未指定時はaccess。DATABASE_BACKENDを互換用に使用 |
| POSTGRES_CONNECTION_URL | 用途別未指定時の基本接続先。POSTGRES_DSNを互換用に使用 |
| POSTGRES_APPEARANCE_CONNECTION_URL | 外観検査DB |
| POSTGRES_DELIVERY_LABEL_CONNECTION_URL | 現品票DB |
| POSTGRES_ARAI_MASTERS_CONNECTION_URL | 製品マスターDB。POSTGRES_PRODUCT_MASTER_CONNECTION_URLを互換用に使用 |
| POSTGRES_SCHEMA | 未指定時public |

AppConfigは設定ディレクトリ・その親、追加ディレクトリ・その親、カレントの.env候補を順に探し、最初の存在するファイルのみ読む。既存プロセス環境変数が優先。exeでは外置き.envを先に探索し、その後バンドル内.envを探索する。外置きファイルの欠損キーを別の.envから補完する構成ではない。

README/.env.exampleはpostgres運用例、コードの既定値とTestsはaccess。これは設定例と既定値の違いであり、それだけで矛盾とはしない。

## 移行・更新資産

| 対象 | 確認できた副作用・境界 |
| --- | --- |
| scripts/migrate_access_to_postgres.py | 旧単一DB向け。既定dry-run、apply時はINSERT。apply-schema、truncateオプションあり。スキーマ・TRUNCATE・テーブル等でcommitを分けるため全体一括復旧ではない |
| docs/appearance_inspection_db、delivery_label_db、delivery_label_search_dbの移行.py | 通常移行は既存テーブルで停止し、作成・投入をトランザクション内で実行。失敗時rollback。verify-onlyはDB件数確認だがログ・結果文書などのファイル副作用は残る |
| 現品票DBのappend-missing | 全列の行値と出現回数を比較して不足行を追記。ただし元件数が移行先件数以下なら比較せず終了。件数一致だけでは内容一致を保証しない |
| docs/arai_masters/create_product_master.py | Excel入力を読み、product_masterをDROPして再作成・投入。commit / rollbackあり |
| scripts/adjust_postgres_sequences.py | 現在はメッセージ表示のみで更新なし |
| database/postgresql/*.sql | 旧単一DBのDDL・制約・CSV投入・検証資産。現在の3DBのDDLとして適用しない |

DB別移行はpsycopg2とDATABASE_URL等を使い、製品マスター作成はxlwingsと別のconfig.envを使う。psycopg2・xlwingsはルートrequirements.txtに含まれない。これらの実行環境、入力、バックアップ、再実行の安全性は未確認。

更新作業の進め方は [database-operations](../.agents/skills/database-operations/SKILL.md) と [共通検証](../.agents/skills/development-workflow/references/data-update-verification.md)。実行許可はRulesのApproval Gateに従う。

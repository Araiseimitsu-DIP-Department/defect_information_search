# Access -> PostgreSQL 移行記録

## 現在の状態

不具合情報検索アプリの PostgreSQL 移行は、アプリ動作確認まで完了しています。

完了済み:

- PostgreSQL スキーマ作成
- Access 6テーブルのデータ投入
- インデックス適用
- 制約適用
- identity sequence 調整
- 検証 SQL 実行
- `PostgresDefectRepository` 実装
- PostgreSQL 英語物理名対応
- `domain_mappers.py` の英語列名対応
- アプリ起動、検索、詳細表示、日付範囲検索、廃棄データ系、Excel 出力の確認

詳細な実行結果は `database/postgresql/migration_notes.md` を参照してください。

## 接続設定

`.env` は次の形式です。

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/defect_information_search
POSTGRES_SCHEMA=public
```

`DB_BACKEND` は `access` または `postgres` を指定します。切り戻し用に `ACCESS_DB_PATH` は残しています。

## PostgreSQL オブジェクト

SQL 一式は `database/postgresql/` にあります。

| ファイル | 役割 |
|---|---|
| `001_schema.sql` | テーブル作成 |
| `002_indexes.sql` | 検索用インデックス |
| `003_constraints.sql` | PK / CHECK / FK 制約 |
| `010_import_from_csv.sql` | CSV投入テンプレート |
| `020_validation.sql` | 件数・重複・空キー・参照欠損検証 |
| `migration_notes.md` | 実行結果 |

作成済みテーブル:

- `defect_records`
- `inspection_records`
- `inspector_master`
- `product_catalog`
- `product_master`
- `qr_history`

## 物理名方針

PostgreSQL は英語物理名へ統一しています。

| Access | PostgreSQL |
|---|---|
| `t_不具合情報` | `defect_records` |
| `t_数値検査記録` | `inspection_records` |
| `t_数値検査員マスタ` | `inspector_master` |
| `t_現品票検索用` | `product_catalog` |
| `t_製品マスタ` | `product_master` |
| `t_QR履歴` | `qr_history` |

代表カラム:

| Access | PostgreSQL |
|---|---|
| `生産ロットID` | `production_lot_id` |
| `品番` | `part_number` |
| `指示日` | `instruction_date` |
| `号機` | `machine_no` |
| `時間` | `work_minutes` |
| `数量` | `quantity` |
| `総不具合数` | `total_defect_count` |
| `不良率` | `defect_rate` |
| `工程コード` | `process_code` |
| `製品番号` | `product_number` |

アプリの表示・Excel出力は従来どおり日本語列名です。PostgreSQL repository は英語列名のまま取得し、`domain_mappers.py` が英語列名を読み取ってドメインモデルへ変換します。

## 実行済み移行結果

最終投入件数:

| テーブル | 件数 |
|---|---:|
| `qr_history` | 108,293 |
| `defect_records` | 154,862 |
| `inspector_master` | 14 |
| `inspection_records` | 24,943 |
| `product_catalog` | 168,837 |
| `product_master` | 1,502 |

identity sequence:

| テーブル | sequence |
|---|---:|
| `defect_records` | 155,048 |
| `inspection_records` | 25,059 |
| `qr_history` | 108,293 |

## 検証結果

最終検証:

- duplicate IDs: 0
- blank `defect_records.part_number`: 3
- blank `defect_records.production_lot_id`: 3
- blank `product_master.product_number`: 0
- blank `inspector_master.inspector_id`: 0
- missing `inspection_records.inspector_id` references: 26
- missing `defect_records.part_number` references in `product_master`: 24,781
- missing `defect_records.production_lot_id` references in `product_catalog`: 12
- `qr_history.process_code = '03'`: 23,370
- app detail search candidates: 106,088

参照欠損は Access 元データ由来のため、外部キーの完全な `VALIDATE CONSTRAINT` は未実施です。履歴データを保持するため、一部 CHECK / FK は `NOT VALID` としています。

## アプリ確認

起動:

```powershell
.\.venv\Scripts\python.exe main.py
```

確認済み:

- アプリ起動
- 品番検索
- 詳細表示
- 時間列表示
- 日付範囲検索
- 廃棄データ系検索
- Excel 出力

自動確認:

```powershell
.\.venv\Scripts\python.exe -m unittest discover
.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('scripts/smoke_test_postgres_repository.py', run_name='__main__')"
```

## 切り戻し

問題があれば `.env` を Access に戻します。

```env
DB_BACKEND=access
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
POSTGRES_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/defect_information_search
POSTGRES_SCHEMA=public
```

Access repository と日本語列名対応 mapper は残しているため、切り戻し可能です。

## 残る運用判断

- Access の利用停止タイミング
- 参照欠損データを補正するか、履歴データとして許容するか
- `product_catalog` を今後も実体テーブルとして更新するか、別システム由来のビューにするか
- Access 切り戻し期間終了後に Access repository を削除するか

## 現時点の完了判定

アプリケーション移行としては完了です。通常起動は `DB_BACKEND=postgres` を前提にします。

今後の変更は、移行作業ではなく運用改善として扱います。

- データ品質補正
- 外部キー制約の `VALIDATE CONSTRAINT`
- Access repository の撤去
- `product_catalog` の更新方式整理

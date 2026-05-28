# Access -> PostgreSQL 移行手順書

## 目的

既存の Access データベース `不具合情報検索.accdb` を PostgreSQL へ移行するための手順書です。

PostgreSQL 側の物理名は英語表記に統一します。Access 側の元テーブル・元カラムは日本語名のまま読み取り、移行スクリプトで PostgreSQL の英語名へマッピングします。

本アプリでは PostgreSQL 移行、アプリ実装、動作確認まで完了済みです。実行結果の詳細は `database/postgresql/migration_notes.md` を参照してください。

## 移行先

```text
host     : 192.168.1.120
database : defect_information_search
schema   : public
encoding : UTF8
timezone : Asia/Tokyo
```

`.env` は次の形式です。

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/defect_information_search
POSTGRES_SCHEMA=public
```

`DB_BACKEND=postgres` が通常運用です。切り戻し用に `ACCESS_DB_PATH` は残します。

## 移行元

```text
\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
```

Access ファイルを読むには、共有フォルダへの読み取り権限が必要です。Access のロックファイル作成が絡む場合があるため、状況によってはフォルダへの書き込み権限も必要です。

## 物理名マッピング

| Access テーブル | PostgreSQL テーブル |
|---|---|
| `t_不具合情報` | `defect_records` |
| `t_数値検査記録` | `inspection_records` |
| `t_数値検査員マスタ` | `inspector_master` |
| `t_現品票検索用` | `product_catalog` |
| `t_製品マスタ` | `product_master` |
| `t_QR履歴` | `qr_history` |

| Access カラム | PostgreSQL カラム | 対象 |
|---|---|---|
| `ID` | `id` | `defect_records`, `inspection_records`, `qr_history` |
| `生産ロットID` | `production_lot_id` | `defect_records`, `inspection_records`, `product_catalog`, `qr_history` |
| `品番` | `part_number` | `defect_records`, `product_catalog` |
| `品名` | `part_name` | `product_catalog` |
| `客先` / `客先名` | `customer_name` | `product_catalog`, `product_master` |
| `指示日` | `instruction_date` | `defect_records`, `product_catalog` |
| `号機` | `machine_no` | `defect_records`, `inspection_records`, `product_catalog` |
| `検査者1` - `検査者5` | `inspector_1` - `inspector_5` | `defect_records` |
| `時間` | `work_minutes` | `defect_records` |
| `数量` | `quantity` | `defect_records`, `product_catalog`, `qr_history` |
| `総不具合数` | `total_defect_count` | `defect_records` |
| `不良率` | `defect_rate` | `defect_records` |
| `その他内容` | `other_detail` | `defect_records` |
| `検査員ID` | `inspector_id` | `inspection_records`, `inspector_master` |
| `検査員名` | `inspector_name` | `inspector_master` |
| `区別` | `category` | `inspector_master` |
| `表示フラグ` | `visible` | `inspector_master` |
| `日付時刻` | `recorded_at` | `inspection_records`, `qr_history` |
| `日付` | `event_at` | `qr_history` |
| `QRコード` | `qr_code` | `qr_history` |
| `工程` | `process` | `qr_history` |
| `位置` | `position` | `qr_history` |
| `工程コード` | `process_code` | `qr_history` |
| `工程名` | `process_name` | `inspection_records`, `qr_history` |
| `更新フラグ` | `updated_flag` | `qr_history` |
| `製品番号` | `product_number` | `product_master` |
| `製品名` | `product_name` | `product_master` |
| `材質` | `material` | `product_master` |
| `単価` | `unit_price` | `product_master` |
| `製品単重` | `unit_weight` | `product_master` |
| `材料識別` | `material_type` | `product_master` |
| `次工程` | `next_process` | `product_master` |

### 不具合内訳

| Access カラム | PostgreSQL カラム |
|---|---|
| `外観キズ` | `appearance_scratch` |
| `圧痕` | `dent` |
| `切粉` | `chip` |
| `毟れ` | `tear` |
| `穴大` | `hole_large` |
| `穴小` | `hole_small` |
| `穴キズ` | `hole_scratch` |
| `バリ` | `burr` |
| `短寸` | `short_length` |
| `面粗` | `rough_surface` |
| `サビ` | `rust` |
| `ボケ` | `blur` |
| `挽目` | `turning_mark` |
| `汚れ` | `stain` |
| `メッキ` | `plating` |
| `落下` | `drop_damage` |
| `フクレ` | `blister` |
| `ツブレ` | `crush` |
| `ボッチ` | `projection` |
| `段差` | `step` |
| `バレル石` | `barrel_stone` |
| `径プラス` | `diameter_plus` |
| `径マイナス` | `diameter_minus` |
| `ゲージ` | `gauge` |
| `異物混入` | `foreign_matter` |
| `形状不良` | `shape_defect` |
| `こすれ` | `rub_mark` |
| `変色シミ` | `discoloration` |
| `材料キズ` | `material_scratch` |
| `ゴミ` | `dust` |
| `その他` | `other` |

## PostgreSQL テーブル

### `defect_records`

| カラム | 型 | 内容 |
|---|---|---|
| `id` | `bigint identity` | 不具合情報ID |
| `production_lot_id` | `varchar(7)` | 生産ロットID |
| `part_number` | `varchar(30)` | 品番 |
| `instruction_date` | `date` | 指示日 |
| `machine_no` | `varchar(5)` | 号機 |
| `inspector_1` - `inspector_5` | `varchar` | 検査者 |
| `work_minutes` | `integer` | 時間 |
| `quantity` | `integer` | 数量 |
| `total_defect_count` | `integer` | 総不具合数 |
| `defect_rate` | `double precision` | 不良率 |
| 不具合内訳列 | `integer` | 各不具合数 |
| `other_detail` | `varchar(10)` | その他内容 |

### `inspection_records`

| カラム | 型 | 内容 |
|---|---|---|
| `id` | `bigint identity` | 数値検査記録ID |
| `recorded_at` | `timestamp` | 日付時刻 |
| `production_lot_id` | `varchar(7)` | 生産ロットID |
| `inspector_id` | `varchar(4)` | 検査員ID |
| `process_name` | `varchar(30)` | 工程名 |
| `machine_no` | `varchar(5)` | 号機 |

### `inspector_master`

| カラム | 型 | 内容 |
|---|---|---|
| `inspector_id` | `varchar(4)` | 検査員ID |
| `inspector_name` | `varchar(5)` | 検査員名 |
| `category` | `varchar(5)` | 区別 |
| `visible` | `boolean` | 表示フラグ |

### `product_catalog`

| カラム | 型 | 内容 |
|---|---|---|
| `production_lot_id` | `varchar(7)` | 生産ロットID |
| `machine_no` | `varchar(5)` | 号機 |
| `part_number` | `varchar(30)` | 品番 |
| `part_name` | `varchar(30)` | 品名 |
| `customer_name` | `varchar(30)` | 客先 |
| `instruction_date` | `date` | 指示日 |
| `quantity` | `integer` | 数量 |

### `product_master`

| カラム | 型 | 内容 |
|---|---|---|
| `product_number` | `varchar(30)` | 製品番号 |
| `product_name` | `varchar(30)` | 製品名 |
| `customer_name` | `varchar(30)` | 客先名 |
| `material` | `varchar(255)` | 材質 |
| `unit_price` | `double precision` | 単価 |
| `unit_weight` | `double precision` | 製品単重 |
| `material_type` | `integer` | 材料識別 |
| `next_process` | `varchar(10)` | 次工程 |

### `qr_history`

| カラム | 型 | 内容 |
|---|---|---|
| `id` | `bigint identity` | QR履歴ID |
| `recorded_at` | `timestamp` | 日付時刻 |
| `qr_code` | `varchar(22)` | QRコード |
| `production_lot_id` | `varchar(7)` | 生産ロットID |
| `event_at` | `timestamp` | 日付 |
| `process` | `varchar(2)` | 工程 |
| `position` | `varchar(2)` | 位置 |
| `quantity` | `integer` | 数量 |
| `process_code` | `varchar(2)` | 工程コード |
| `process_name` | `varchar(30)` | 工程名 |
| `updated_flag` | `varchar(1)` | 更新フラグ |

## SQL ファイル

| ファイル | 役割 |
|---|---|
| `database/postgresql/001_schema.sql` | 英語物理名のテーブル作成 |
| `database/postgresql/002_indexes.sql` | 検索用インデックス |
| `database/postgresql/003_constraints.sql` | PK / CHECK / FK 制約 |
| `database/postgresql/010_import_from_csv.sql` | CSVインポート用テンプレート |
| `database/postgresql/020_validation.sql` | 件数・NULL・重複・参照欠損検証 |
| `database/postgresql/migration_notes.md` | 実行結果メモ |

## 本番移行手順

### 1. 事前停止

Access アプリ利用者へ停止時間を連絡し、移行中は Access 側を更新しない状態にします。

### 2. バックアップ

Access ファイルと PostgreSQL の既存DBをバックアップします。

### 3. dry-run

PostgreSQL へ書き込まず、Access から読み取れるか確認します。

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

最終実行時の例:

```text
qr_history: 108,188 rows
defect_records: 154,836 rows
inspector_master: 14 rows
inspection_records: 24,943 rows
product_catalog: 168,834 rows
product_master: 1,502 rows
```

### 4. 本投入

`--apply-schema --truncate` でテーブルを初期化して再投入します。

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate
```

このスクリプトは次を行います。

- Access 6テーブルを読み取り
- PostgreSQL 英語物理名へ変換して投入
- 日付、数値、boolean、NULL / 空文字を正規化
- `defect_records.id`, `inspection_records.id`, `qr_history.id` の identity sequence 調整

### 5. インデックス作成

```text
database/postgresql/002_indexes.sql
```

### 6. 制約適用

```text
database/postgresql/003_constraints.sql
```

履歴データに参照欠損や負数が含まれるため、一部 CHECK / FK は `NOT VALID` としています。完全な FK 検証はデータ品質補正後に行います。

### 7. 検証

```text
database/postgresql/020_validation.sql
```

確認項目:

- 6テーブルの件数
- `part_number`, `production_lot_id`, `product_number`, `inspector_id` の空キー
- `id` の重複
- `inspection_records.inspector_id -> inspector_master.inspector_id` の参照欠損
- `defect_records.part_number -> product_master.product_number` の参照欠損
- `defect_records.production_lot_id -> product_catalog.production_lot_id` の参照欠損
- `qr_history.process_code = '03'` の廃棄データ対象件数
- アプリ用の詳細検索候補件数

最終確認済み例:

```text
qr_history: 108293
defect_records: 154862
inspector_master: 14
inspection_records: 24943
product_catalog: 168837
product_master: 1502
duplicate IDs: 0
```

### 8. アプリ確認

`.env` を `DB_BACKEND=postgres` にして `main.py` を起動します。

```powershell
.\.venv\Scripts\python.exe main.py
```

確認する操作:

- アプリ起動
- 品番検索
- 詳細表示
- 時間列表示
- 日付範囲検索
- 廃棄データ系検索
- Excel 出力

## アプリ側の実装

PostgreSQL 側は次の実装が英語物理名を参照します。

```text
src/defect_information_search/infrastructure/postgres/defect_repository.py
src/defect_information_search/infrastructure/mappers/domain_mappers.py
```

PostgreSQL repository は英語列名のまま取得し、`domain_mappers.py` がドメインモデルへ変換します。アプリ画面と Excel 出力は従来どおり日本語列名です。

Access 側の repository は日本語物理名の Access DB を扱うため、切り戻し用に残しています。

## 切り戻し

問題があれば `.env` を Access に戻します。

```env
DB_BACKEND=access
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/defect_information_search
POSTGRES_SCHEMA=public
```

切り戻し後、PostgreSQL 側のデータまたは repository 実装を修正して再移行します。

## 現時点の完了判定

アプリケーション移行としては完了です。通常起動は `DB_BACKEND=postgres` を前提にします。

今後の変更は、移行作業ではなく運用改善として扱います。

- データ品質補正
- 外部キー制約の `VALIDATE CONSTRAINT`
- Access repository の撤去
- `product_catalog` の更新方式整理

## 本番移行を依頼するときの指示例

```text
PostgreSQL本番移行を実行してください。
手順は docs/postgresql-migration.md と database/postgresql/migration_notes.md に従ってください。
実行前に dry-run を行い、件数を確認してから --apply-schema --truncate で本投入してください。
投入後、002_indexes.sql、003_constraints.sql、020_validation.sql を実行し、結果を migration_notes.md に記録してください。
アプリ確認は DB_BACKEND=postgres に切り替えて main.py から実施してください。
```

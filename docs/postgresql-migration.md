# PostgreSQL 移行・運用手順書

## 目的

不具合情報検索アプリを PostgreSQL 運用するための接続先、テーブル対応、アプリ側処理方針をまとめます。

現在の運用では、旧 Access のクエリを PostgreSQL ビューで再現しません。各DBの移行済みテーブルを Python repository が直接参照し、必要な結合・集計・表示用変換は Python 側で処理します。

## 現在の移行先

```text
host   : 192.168.1.120
schema : public
```

| 用途 | PostgreSQL DB | 主なテーブル |
|---|---|---|
| 外観検査・不具合情報 | `appearance_inspection_db` | `defect_information`, `numeric_inspection_records`, `numeric_inspector_master` |
| 現品票・QR履歴 | `delivery_label_db` | `qr_history` |
| 現品票検索 | `delivery_label_search_db` | `delivery_label_search` |
| ARAI製品マスター | `arai_masters` | `product_master` |

## .env

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/appearance_inspection_db
POSTGRES_APPEARANCE_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/appearance_inspection_db
POSTGRES_DELIVERY_LABEL_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/delivery_label_db
POSTGRES_DELIVERY_LABEL_SEARCH_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/delivery_label_search_db
POSTGRES_ARAI_MASTERS_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/arai_masters
POSTGRES_SCHEMA=public
```

`DB_BACKEND=postgres` が通常運用です。切り戻し用に `ACCESS_DB_PATH` は残します。

`POSTGRES_CONNECTION_URL` は互換用の基本接続先です。アプリ本体は用途別の接続先を優先します。

## 移行元資料

各DBのDDL、メタ情報、マッピング、移行結果は次に保管しています。

| フォルダ | 内容 |
|---|---|
| `docs/appearance_inspection_db` | 外観検査記録DBの移行資料 |
| `docs/delivery_label_db` | 現品票DBの移行資料 |
| `docs/delivery_label_search_db` | 現品票検索DBの移行資料 |
| `docs/arai_masters` | ARAI製品マスターの移行資料 |

## アプリ参照マッピング

### 品番検索

`delivery_label_search_db.public.delivery_label_search` を参照します。

| アプリ用途 | PostgreSQLカラム |
|---|---|
| 品番 | `product_code` |
| 品名 | `product_name` |
| 客先 | `customer` |
| 指示日 | `instruction_date` |
| 数量 | `quantity` |

### 不具合情報

`appearance_inspection_db.public.defect_information` を参照します。アプリ内部の既存モデルに合わせるため、repository で列名を変換します。

| アプリ側の意味 | PostgreSQLカラム |
|---|---|
| ID | `id` |
| 生産ロットID | `production_lot_id` |
| 品番 | `product_code` |
| 指示日 | `instruction_date` |
| 号機 | `machine_no` |
| 検査者1-5 | `inspector_1` - `inspector_5` |
| 時間 | `time_value` |
| 数量 | `quantity` |
| 総不具合数 | `total_defect_count` |
| 不良率 | `defect_rate` |
| その他内容 | `other_detail` |

### 不具合内訳

| 表示項目 | PostgreSQLカラム |
|---|---|
| 外観キズ | `appearance_scratch` |
| 圧痕 | `dent` |
| 切粉 | `cutting_chip` |
| 毟れ | `mushire` |
| 穴大 | `oversized_hole` |
| 穴小 | `undersized_hole` |
| 穴キズ | `hole_scratch` |
| バリ | `burr` |
| 短寸 | `short_length` |
| 面粗 | `rough_surface` |
| サビ | `rust` |
| ボケ | `blur` |
| 挽目 | `turning_mark` |
| 汚れ | `stain` |
| メッキ | `plating` |
| 落下 | `dropped` |
| フクレ | `swelling` |
| ツブレ | `crush` |
| ボッチ | `bump` |
| 段差 | `step` |
| バレル石 | `barrel_stone` |
| 径プラス | `diameter_plus` |
| 径マイナス | `diameter_minus` |
| ゲージ | `gauge` |
| 異物混入 | `foreign_matter` |
| 形状不良 | `shape_defect` |
| こすれ | `abrasion` |
| 変色シミ | `discoloration_stain` |
| 材料キズ | `material_scratch` |
| ゴミ | `dust` |
| その他 | `other` |

### 数値検査員名

Access のクエリ相当の検査員名補完は、PostgreSQL ビューではなく Python で行います。

1. `defect_information.production_lot_id` を取得
2. `numeric_inspection_records` からロットごとの検査員IDを取得
3. `numeric_inspector_master` から検査員名を取得
4. Python 側で不具合明細へ結合

### QR履歴

廃棄データ対象ロットは `delivery_label_db.public.qr_history` を参照します。

| アプリ用途 | PostgreSQLカラム |
|---|---|
| 生産ロットID | `production_lot_id` |
| 日付 | `date_value` |
| 工程コード | `process_code` |

廃棄データでは `process_code = '03'` を対象にします。

### 製品マスター

旧 Access の `t_製品マスタ` は、現在は `arai_masters.public.product_master` として扱います。アプリでは必要なカラムのみ取得します。

| アプリ用途 | PostgreSQLカラム |
|---|---|
| 製品番号 | `product_no` |
| 製品名 | `product_name` |
| 客先名 | `customer_name` |
| 材質 | `material_and_diameter` |
| 単価 | `unit_price` |
| 製品単重 | `unit_weight` |
| 材料識別 | `material_identification` |
| 次工程 | `next_process` |

`product_master.id` は主キーですが、アプリの品番突合は `product_no` で行います。

## アプリ側の実装

PostgreSQL 側は次の実装が参照します。

```text
src/defect_information_search/config.py
src/defect_information_search/infrastructure/postgres/defect_repository.py
src/defect_information_search/infrastructure/mappers/domain_mappers.py
```

`PostgresDefectRepository` は各DBへ必要に応じて接続し、英語列名を既存ドメインモデルへ変換します。画面と Excel 出力は従来どおり日本語列名です。

## 検証手順

ユニットテスト:

```powershell
.\.venv\Scripts\python.exe -m unittest discover
```

PostgreSQL 実データスモーク:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test_postgres_repository.py
```

確認済み例:

```text
products=6
defects_for_part=23644
defects_for_part_non_null_work_minutes=23614
defects_between=106373
qr_lots=23809
lot_defects=5
product_masters=1
iter_columns=47
iter_sample_rows=3
```

## アプリ確認

`.env` を `DB_BACKEND=postgres` にして `main.py` を起動します。

```powershell
.\.venv\Scripts\python.exe main.py
```

確認する操作:

- アプリ起動
- 品番検索
- 詳細表示
- 号機絞り込み
- 日付範囲検索
- Excel 出力
- 集計データ出力
- 廃棄データ出力

## 切り戻し

問題があれば `.env` を Access に戻します。

```env
DB_BACKEND=access
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\不具合情報検索.accdb
```

Access repository は切り戻し期間のために残しています。

## 旧単一DB移行資産について

`database/postgresql/*.sql` と `scripts/migrate_access_to_postgres.py` は、旧 `defect_information_search` 単一DBへ6テーブルを統合していた時期の資産です。現在の通常運用アプリは、指定4DBの移行済みテーブルを直接参照します。

今後の通常運用で移行を再実行する場合は、各DB別フォルダ内の移行スクリプトとマッピングを基準にしてください。

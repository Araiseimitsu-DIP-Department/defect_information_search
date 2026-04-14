# 不具合情報検索 データ移行マップ

`docs/不具合情報検索_meta.md` を基準にした、Access から PostgreSQL へ移行するための対応表です。

## 1. テーブル対応

| Access テーブル | 業務概念 | PostgreSQL 側の想定 |
|---|---|---|
| `t_QR履歴` | `QrHistoryItem` | `qr_history` |
| `t_不具合情報` | `DefectRecord` | `defect_records` |
| `t_数値検査員マスタ` | `InspectorMasterItem` | `inspector_master` |
| `t_数値検査記録` | `InspectionRecord` | `inspection_records` |
| `t_現品票検索用` | `ProductCatalogItem` | `product_catalog` |
| `t_製品マスタ` | `ProductMasterItem` | `product_master` |

## 2. 主キー候補

| Access テーブル | 主キー候補 | 備考 |
|---|---|---|
| `t_不具合情報` | `ID` | COUNTER 相当。PostgreSQL では `BIGSERIAL` か `IDENTITY` に置換 |
| `t_数値検査記録` | `ID` | 同上 |
| `t_数値検査員マスタ` | `検査員ID` | 業務コードとして扱う |
| `t_製品マスタ` | `製品番号` | 製品コード |
| `t_QR履歴` | 直接の一意キーなし | `生産ロットID + 日付時刻 + 工程コード` などで複合候補を設計 |
| `t_現品票検索用` | 直接の一意キーなし | 検索用ビュー相当として扱う |

## 3. 推定リレーション

| 子テーブル | 親テーブル | 関連列 |
|---|---|---|
| `t_不具合情報` | `t_現品票検索用` | `生産ロットID`, `品番` |
| `t_不具合情報` | `t_製品マスタ` | `品番` -> `製品番号` |
| `t_数値検査記録` | `t_数値検査員マスタ` | `検査員ID` |
| `t_QR履歴` | `t_現品票検索用` | `生産ロットID` |

## 4. 移行時の注意

- Access 側は FK がなくても、PostgreSQL 側では参照整合性を設計する
- `VARCHAR` で入っている列は、移行時に `date` / `timestamp` / `numeric` / `boolean` へ寄せる
- `COUNTER` は PostgreSQL の `BIGSERIAL` または `GENERATED ... AS IDENTITY` に置き換える
- `t_現品票検索用` は参照テーブルというより検索用ビューの可能性があるため、実体テーブルかビューかを移行時に判定する

## 5. 今の実装との接続

- `AccessDefectRepository` は当面 Access を読む実装
- `PostgresDefectRepository` は将来の差し替え先
- `domain/models.py` は業務概念を固定する場所
- `infrastructure/mappers/domain_mappers.py` は列名差分吸収の場所


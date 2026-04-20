# Access -> PostgreSQL 移行メモ

## 目的

本書は、`defect_information_search` の現行実装と、`docs/不具合情報検索_meta.md` から読み取れる Access スキーマをもとに、将来 Microsoft Access から PostgreSQL へ移行する際の設計メモを整理したものです。

- 現時点の正式稼働 DB は Access (`.accdb`)
- 現行 Python アプリは Access のテーブル名・カラム名をほぼそのまま利用している
- 本書は「初回移行で業務を止めずに動かす」ことを優先した暫定設計である
- 不明点は未確認として明記し、推測だけで確定扱いしない

## 現行アプリの構成

```text
defect_information_search/
├─ main.py
├─ build_exe.ps1
├─ requirements.txt
├─ .env
├─ docs/
│  └─ 工業検査とエラー検出アイコン.png
└─ src/
   └─ defect_information_search/
      ├─ app.py
      ├─ config.py
      ├─ domain/
      │  └─ models.py
      ├─ application/
      │  └─ ports/
      │     └─ defect_repository.py
      ├─ infrastructure/
      │  ├─ access/
      │  │  └─ defect_repository.py
      │  └─ postgres/
      │     └─ defect_repository.py
      ├─ services/
      │  ├─ defect_service.py
      │  └─ export_service.py
      └─ webview/
         ├─ app.py
         ├─ bridge.py
         └─ assets/
            ├─ index.html
            ├─ app.js
            └─ styles.css
```

## 現在の処理サマリ

現行アプリは、不具合情報の検索・集計・Excel 出力を行う Windows 向けデスクトップアプリです。

### 画面機能

- 品番候補検索
- 候補一覧の表示
- 候補行のダブルクリックによる詳細表示
- 号機での絞り込み
- 不具合数・不良率・不具合内訳の集計表示
- 表示中データの Excel 出力
- 日付範囲での全品番エクスポート
- 集計データ出力
- 廃棄データ出力

### 現行の DB 依存ポイント

`src/defect_information_search/infrastructure/access/defect_repository.py` が Access SQL を直接実行している。

現行の主な参照元は次の通り。

- `t_現品票検索用`
  - 品番候補検索に使用
  - 参照列は `品番`, `品名`, `客先`
- `t_不具合情報`
  - 詳細検索、集計、全件出力の中心テーブル
  - 参照列は `生産ロットID`, `品番`, `指示日`, `号機`, `検査者1` から `検査者5`, `時間`, `数量`, `総不具合数`, `不良率`, 各不具合項目, `その他内容`
- `t_数値検査記録`
  - 不具合詳細に対する数値検査員取得に使用
- `t_数値検査員マスタ`
  - 数値検査員名の解決に使用
- `t_QR履歴`
  - 廃棄データの対象ロット抽出に使用
- `t_製品マスタ`
  - 集計データと廃棄データの金額・重量計算に使用

### Python 側の論理モデル

`src/defect_information_search/domain/models.py` の現在の論理モデルは次の通り。

- `ProductCatalogItem`
- `ProductMasterItem`
- `QrHistoryItem`
- `InspectorMasterItem`
- `InspectionRecord`
- `DefectRecord`

`DefectRecord` は、`数値検査員` を `numeric_inspector` として保持する。

## PostgreSQL 移行方針

### 方針 1: 初回移行では物理名をなるべく維持する

現行コードは日本語テーブル名・日本語カラム名に強く依存している。
初回移行では、以下を優先する。

- テーブル名は Access と同じ名前を維持する
- カラム名も Access と同じ名前を維持する
- PostgreSQL でも UTF-8 の日本語識別子を許容する

この方針にすると、アプリ改修を「接続処理」「SQL 方言差分」「採番・ID 取得」に絞りやすい。

### 方針 2: 一時テーブルはできるだけ廃止する

現行 Python 実装では、画面表示や Excel 出力はメモリ上の DataFrame で代替できる。
初回移行では、旧 Access 由来の一時テーブルは原則作らない方がよい。

候補:

- `t_請求書Tmp`
- `t_納品書`
- `t_納品書データ`
- 帳票印刷用の補助テーブル類

### 方針 3: Access 固有構文を排除する

移行時に置換が必要な代表例。

- `SELECT @@IDENTITY` -> `INSERT ... RETURNING`
- `DELETE * FROM ...` -> `DELETE FROM ...`
- Access の日付比較や文字列比較への依存を PostgreSQL の厳密な型比較に置換
- NULL と空文字の曖昧な扱いをルール化する

## 推奨 DB 設定

### DB 基本設定

```text
db_name: defect_information_search
encoding: UTF8
lc_collate: ja_JP.UTF-8
lc_ctype: ja_JP.UTF-8
timezone: Asia/Tokyo
default_schema: public
```

### 接続設定案

`.env` の現在の実装は Access / PostgreSQL 切替に対応している。
PostgreSQL 側の候補は次のような形。

```text
DATABASE_BACKEND=postgres
POSTGRES_DSN=host=127.0.0.1 port=5432 dbname=defect_information_search user=app_user password=your_password
```

## テーブル設計

以下は、`docs/不具合情報検索_meta.md` と現行 Python 実装から見える範囲で整理した、移行時の推奨テーブル案である。

### 1. `t_不具合情報`

現行アプリの中心テーブル。検索・集計・一覧表示・全件出力の主データ。

#### 用途

- 品番候補からの詳細表示
- 号機絞り込み
- 集計値・不具合内訳表示
- 表示中データの Excel 出力
- 日付範囲での全件出力

#### 現行で参照している主な列

- `ID`
- `生産ロットID`
- `品番`
- `指示日`
- `号機`
- `検査者1` から `検査者5`
- `時間`
- `数量`
- `総不具合数`
- `不良率`
- 各不具合項目
- `その他内容`

#### 推奨カラム

| カラム | 推奨型 | 必須 | 備考 |
|---|---|---:|---|
| ID | bigserial | Yes | 主キー |
| 生産ロットID | varchar(7) | Yes | ロット識別 |
| 品番 | varchar(30) | Yes | 検索キー |
| 指示日 | date | Yes | 日付範囲検索に使用 |
| 号機 | varchar(5) | No | 画面フィルタ用 |
| 検査者1 | varchar(6) | No |  |
| 検査者2 | varchar(6) | No |  |
| 検査者3 | varchar(6) | No |  |
| 検査者4 | varchar(6) | No |  |
| 検査者5 | varchar(20) | No |  |
| 時間 | integer | No | 空欄を許容 |
| 数量 | integer | No | 空欄を許容 |
| 総不具合数 | integer | No | 空欄を許容 |
| 不良率 | double precision | No | 表示は 0.0% 系 |
| 外観キズ | integer | No | 不具合内訳 |
| 圧痕 | integer | No | 不具合内訳 |
| 切粉 | integer | No | 不具合内訳 |
| 毟れ | integer | No | 不具合内訳 |
| 穴大 | integer | No | 不具合内訳 |
| 穴小 | integer | No | 不具合内訳 |
| 穴キズ | integer | No | 不具合内訳 |
| バリ | integer | No | 不具合内訳 |
| 短寸 | integer | No | 不具合内訳 |
| 面粗 | integer | No | 不具合内訳 |
| サビ | integer | No | 不具合内訳 |
| ボケ | integer | No | 不具合内訳 |
| 挽目 | integer | No | 不具合内訳 |
| 汚れ | integer | No | 不具合内訳 |
| メッキ | integer | No | 不具合内訳 |
| 落下 | integer | No | 不具合内訳 |
| フクレ | integer | No | 不具合内訳 |
| ツブレ | integer | No | 不具合内訳 |
| ボッチ | integer | No | 不具合内訳 |
| 段差 | integer | No | 不具合内訳 |
| バレル石 | integer | No | 不具合内訳 |
| 径プラス | integer | No | 不具合内訳 |
| 径マイナス | integer | No | 不具合内訳 |
| ゲージ | integer | No | 不具合内訳 |
| 異物混入 | integer | No | 不具合内訳 |
| 形状不良 | integer | No | 不具合内訳 |
| こすれ | integer | No | 不具合内訳 |
| 変色シミ | integer | No | 不具合内訳 |
| 材料キズ | integer | No | 不具合内訳 |
| ゴミ | integer | No | 不具合内訳 |
| その他 | integer | No | 不具合内訳 |
| その他内容 | varchar(10) | No | 補足文言 |

#### 推奨制約

- `PRIMARY KEY (ID)`
- `CHECK (数量 >= 0 OR 数量 IS NULL)`
- `CHECK (総不具合数 >= 0 OR 総不具合数 IS NULL)`
- `CHECK (不良率 >= 0 OR 不良率 IS NULL)`

#### 推奨インデックス

- `INDEX ON (品番)`
- `INDEX ON (指示日)`
- `INDEX ON (号機)`
- `INDEX ON (生産ロットID)`

#### 備考

- 現行アプリでは `find_defects_for_part` と `find_defects_between` の両方で使用する
- `数値検査員` は別テーブル JOIN で補完する

### 2. `t_数値検査記録`

数値検査員の実績記録テーブル。

#### 推奨カラム

| カラム | 推奨型 | 必須 | 備考 |
|---|---|---:|---|
| ID | bigserial | Yes | 主キー |
| 日付時刻 | timestamp | No |  |
| 生産ロットID | varchar(7) | Yes | `t_不具合情報` と突合 |
| 検査員ID | varchar(4) | No | `t_数値検査員マスタ` 参照 |
| 工程名 | varchar(30) | No |  |
| 号機 | varchar(5) | No |  |

#### 推奨制約

- `PRIMARY KEY (ID)`
- `INDEX ON (生産ロットID)`
- `INDEX ON (検査員ID)`

#### 備考

- 現行 Access では `t_不具合情報` に JOIN して `数値検査員` を取得している
- PostgreSQL でも `INSERT ... RETURNING ID` に置換する

### 3. `t_数値検査員マスタ`

数値検査員名の参照マスタ。

#### 推奨カラム

| カラム | 推奨型 | 必須 | 備考 |
|---|---|---:|---|
| 検査員ID | varchar(4) | Yes | 主キー候補 |
| 検査員名 | varchar(20) | Yes | 画面表示名 |
| 区別 | varchar(5) | No |  |
| 表示フラグ | boolean | Yes | 表示可否 |

#### 推奨制約

- `PRIMARY KEY (検査員ID)`
- `CHECK (表示フラグ IN (true, false))`

#### 推奨インデックス

- `INDEX ON (検査員名)`

### 4. `t_現品票検索用`

品番候補検索の元テーブル。

#### 現行で使う列

- `生産ロットID`
- `号機`
- `品番`
- `品名`
- `客先`
- `指示日`
- `数量`

#### 推奨カラム

| カラム | 推奨型 | 必須 | 備考 |
|---|---|---:|---|
| 生産ロットID | varchar(7) | Yes |  |
| 号機 | varchar(5) | No |  |
| 品番 | varchar(30) | Yes | 候補検索キー |
| 品名 | varchar(30) | No |  |
| 客先 | varchar(30) | No |  |
| 指示日 | date | No |  |
| 数量 | integer | No |  |

#### 推奨制約

- 実装次第で `PRIMARY KEY` は不要
- 品番の検索効率を重視

#### 推奨インデックス

- `INDEX ON (品番)`
- `INDEX ON (品名)`
- `INDEX ON (客先)`

### 5. `t_製品マスタ`

集計・廃棄データで金額や重量を補完するマスタ。

#### 現行で使う列

- `製品番号`
- `製品名`
- `客先名`
- `材質`
- `単価`
- `製品単重`
- `材料識別`
- `次工程`

#### 推奨カラム

| カラム | 推奨型 | 必須 | 備考 |
|---|---|---:|---|
| 製品番号 | varchar(30) | Yes |  |
| 製品名 | varchar(30) | No |  |
| 客先名 | varchar(30) | No |  |
| 材質 | varchar(255) | No |  |
| 単価 | numeric(12,2) | No |  |
| 製品単重 | numeric(12,3) | No |  |
| 材料識別 | integer | No |  |
| 次工程 | varchar(10) | No |  |

#### 推奨制約

- `PRIMARY KEY (製品番号)`

#### 推奨インデックス

- `INDEX ON (客先名)`
- `INDEX ON (材質)`
- `INDEX ON (次工程)`

### 6. `t_QR履歴`

廃棄データの対象ロット抽出に使う履歴テーブル。

#### 現行で使う列

- `生産ロットID`
- `日付`
- `工程コード`

#### 推奨カラム

| カラム | 推奨型 | 必須 | 備考 |
|---|---|---:|---|
| 日付時刻 | timestamp | No |  |
| QRコード | varchar(22) | No |  |
| 生産ロットID | varchar(7) | Yes |  |
| 日付 | timestamp | No |  |
| 工程 | varchar(2) | No |  |
| 位置 | varchar(2) | No |  |
| 数量 | integer | No |  |
| 工程コード | varchar(2) | No |  |
| 工程名 | varchar(30) | No |  |
| 更新フラグ | varchar(1) | No |  |

#### 推奨インデックス

- `INDEX ON (日付)`
- `INDEX ON (工程コード)`
- `INDEX ON (生産ロットID)`

## 現行 Python 実装との対応

### Repository

`src/defect_information_search/infrastructure/access/defect_repository.py` の Access 実装は、PostgreSQL へ移行後も同じ repository インターフェースを維持する前提である。

現在の repository メソッドと DB の対応は次の通り。

- `find_products(keyword)`
  - `t_現品票検索用`
- `find_defects_for_part(part_number, date_from, date_to)`
  - `t_不具合情報`
  - `t_数値検査記録`
  - `t_数値検査員マスタ`
- `find_defects_between(date_from, date_to)`
  - `t_不具合情報`
- `find_qr_history_lots(date_from, date_to)`
  - `t_QR履歴`
- `find_defects_for_lots(lot_ids)`
  - `t_不具合情報`
- `find_product_master_for_parts(part_numbers)`
  - `t_製品マスタ`
- `iter_all_defects(date_from, date_to)`
  - `t_不具合情報`

### Service

`src/defect_information_search/services/defect_service.py` は、DB 差し替え時も保持したい処理を持っている。

- 候補一覧の生成
- 詳細検索結果の整形
- 号機フィルタリング
- 集計値の算出
- 廃棄量・廃棄金額の計算
- Excel 出力用のデータ整形

### WebView

`src/defect_information_search/webview/` は UI 層であり、DB 移行時は基本的に変更不要。

- `app.py`
  - `.env` を読み込む
  - Access / PostgreSQL を切り替える
- `bridge.py`
  - UI 操作を service 層へ伝える
- `assets/`
  - 検索条件
  - 候補一覧
  - 集計表示
  - 詳細一覧
  - エクスポートボタン

## PostgreSQL 移行で必要な SQL 方針

### 1. 採番

Access の `@@IDENTITY` 相当は PostgreSQL では `RETURNING` へ置換する。

```sql
INSERT INTO "t_数値検査記録" (
  "日付時刻", "生産ロットID", "検査員ID", "工程名", "号機"
)
VALUES (
  :日付時刻, :生産ロットID, :検査員ID, :工程名, :号機
)
RETURNING "ID";
```

### 2. NULL と空文字

Access では空文字と NULL が混在しやすい。
PostgreSQL へ入れる前に、次の列はルールを決めて正規化した方がよい。

- `品番`
- `品名`
- `客先`
- `検査者1` から `検査者5`
- `その他内容`
- `号機`

### 3. 日付比較

Access の日付比較に依存せず、PostgreSQL では `date` / `timestamp` として比較する。

### 4. 部分一致検索

現行の品番候補検索は `LIKE '%keyword%'` を使っている。
PostgreSQL へ移行後も同じ挙動を維持するなら、初回はそのまま `LIKE` でよい。
件数が増える場合は `pg_trgm` を検討する。

## トランザクション要件

現行アプリでは検索中心だが、将来 PostgreSQL に移す際も、以下は 1 トランザクションで扱うべきである。

- 採番 + 登録
- 明細追加 + 親テーブル更新
- 一括削除 + 再登録
- 集計保存

## 推奨インデックス優先度

### 最優先

- `t_不具合情報(品番)`
- `t_不具合情報(指示日)`
- `t_不具合情報(生産ロットID)`
- `t_数値検査記録(生産ロットID)`
- `t_数値検査員マスタ(検査員ID)`
- `t_現品票検索用(品番)`
- `t_製品マスタ(製品番号)`

### 次点

- `t_不具合情報(号機)`
- `t_不具合情報(総不具合数)`
- `t_QR履歴(工程コード)`
- `t_QR履歴(日付)`

## 未確認事項

`docs/不具合情報検索_meta.md` からは列定義がかなり見えるが、以下はまだ最終確定ではない。

- `t_不具合情報` の主キー運用
- `t_現品票検索用` の元データと更新頻度
- `t_QR履歴` の更新元と保持ルール
- `t_数値検査員マスタ` の表示フラグの厳密な意味
- `t_製品マスタ` の `材料識別` と `次工程` の許容値
- 空文字と NULL の正規化ルール
- 号機コードの完全な値一覧
- `その他内容` の最大長と実データ分布

## 初回移行で最低限必要なテーブル

現行 Python アプリを PostgreSQL に切り替えて、検索・集計・出力を動かすだけなら、まずは次を優先する。

- `t_不具合情報`
- `t_数値検査記録`
- `t_数値検査員マスタ`
- `t_現品票検索用`
- `t_製品マスタ`
- `t_QR履歴`

## 次にやるとよいこと

1. Access 実 DB から制約・索引・実データの NULL 分布を確認する
2. PostgreSQL 用 DDL を別ファイルで確定する
3. `src/defect_information_search/infrastructure/postgres/defect_repository.py` を実装する
4. Access / PostgreSQL 切替の自動テストを追加する


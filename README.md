# 不具合情報検索

外観検査の不具合情報を検索し、集計確認と Excel 出力を行う Windows 向けデスクトップアプリです。

画面は `pywebview` + `Edge WebView2`、業務ロジックは service / repository 層で構成しています。通常運用DBは PostgreSQL です。Access repository は切り戻し用に残しています。

## 構成

```text
defect_information_search/
├─ main.py
├─ build_exe.ps1
├─ requirements.txt
├─ .env.example
├─ docs/
│  ├─ postgresql-migration.md
│  ├─ appearance_inspection_db/
│  ├─ arai_masters/
│  ├─ delivery_label_db/
├─ scripts/
│  └─ smoke_test_postgres_repository.py
└─ src/
   └─ defect_information_search/
      ├─ config.py
      ├─ infrastructure/
      │  ├─ access/
      │  ├─ postgres/
      │  └─ mappers/
      ├─ services/
      └─ webview/
```

## 接続設定

`.env.example` を参考に `.env` を作成します。

```env
ACCESS_DB_PATH=C:\path\to\不具合情報検索.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/appearance_inspection_db
POSTGRES_APPEARANCE_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/appearance_inspection_db
POSTGRES_DELIVERY_LABEL_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/delivery_label_db
POSTGRES_ARAI_MASTERS_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/arai_masters
POSTGRES_SCHEMA=public
```

- `DB_BACKEND=postgres`: PostgreSQL を使用します。
- `DB_BACKEND=access`: Access へ切り戻します。
- `POSTGRES_CONNECTION_URL`: 互換用の基本接続先です。通常は `appearance_inspection_db` を指定します。
- `POSTGRES_APPEARANCE_CONNECTION_URL`: 外観検査記録DBです。不具合情報と数値検査員情報を参照します。
- `POSTGRES_DELIVERY_LABEL_CONNECTION_URL`: 現品票DBです。QR履歴と品番検索候補を参照します。
- `POSTGRES_ARAI_MASTERS_CONNECTION_URL`: ARAIマスターDBです。`product_master` から必要カラムのみ参照します。

`.env` は認証情報を含むため Git 管理しません。

## 実行

```powershell
.\.venv\Scripts\python.exe .\main.py
```

## テスト

```powershell
.\.venv\Scripts\python.exe -m unittest discover
```

PostgreSQL repository の実データ確認:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test_postgres_repository.py
```

## PostgreSQL 運用

現在のアプリは、Access のクエリを PostgreSQL ビューで再現せず、Python repository / service 側で必要な結合・補完を行います。

主な参照先:

| 用途 | DB | テーブル |
|---|---|---|
| 不具合検索・集計 | `appearance_inspection_db` | `defect_information` |
| 数値検査員名補完 | `appearance_inspection_db` | `numeric_inspection_records`, `numeric_inspector_master` |
| QR廃棄対象ロット | `delivery_label_db` | `qr_history` |
| 品番検索候補 | `delivery_label_db` | `delivery_label_history` |
| 製品マスター | `arai_masters` | `product_master` |

`arai_masters.product_master` は旧 Access の `t_製品マスタ` 相当として扱います。アプリではマッピングメモに基づき、`product_no`, `product_name`, `customer_name`, `material_and_diameter`, `unit_price`, `unit_weight`, `material_identification`, `next_process` など必要なカラムだけを取得します。

詳細は [docs/postgresql-migration.md](docs/postgresql-migration.md) と各DB別のマッピングメモを参照してください。

## ビルド

onefile の exe は次で作成します。

```powershell
.\build_exe.ps1
```

ビルドスクリプトは `docs\app_icon.png` から `.ico` を生成し、`.env` を同梱したうえで PyInstaller onefile を作成します。

最終成果物は `dist\不具合情報検索.exe` です。

## 配布時の前提

- 配布先 PC に Microsoft Edge WebView2 Runtime が必要です。
- PostgreSQL サーバー `192.168.1.120:5432` の4DBへ接続できる必要があります。
- 切り戻し運用を行う場合のみ、`.env` の `ACCESS_DB_PATH` へ到達できる必要があります。

## 主な機能

- 品番候補検索（PostgreSQLでは大文字小文字を区別せず、例: `3d025` で `3D025...` を候補表示）
- 候補一覧からの詳細表示
- 号機絞り込み
- 合計値・不具合内訳表示
- 表示中データの Excel 出力
- 日付範囲での全品番エクスポート
- 集計データ出力
- 廃棄データ出力

## UI Design

- `docs/DESIGN.md` is the primary UI reference for the WebView screen tokens, spacing, cards, tables, and buttons.
- This screen has no page menu, so the left sidebar is not used.
- The ARAI logo is placed in the title row and bundled from `src/defect_information_search/webview/assets/arai_logo.png`.
- The footer is rendered at the bottom of the WebView with the standard copyright text.

## Display Size Notes

- The distributed WebView window minimum size is `960x640`.
- On normal-height screens, the app keeps the fixed full-window layout and the product/detail tables scroll inside their panels.
- On short screens, including `1366x768`, `1280x720`, and Windows display scale `125%` / `150%` equivalent viewports, the app switches to document-level vertical scrolling so the search fields, tables, export buttons, and footer remain reachable.
- Recommended manual checks: start the app, resize the window to around `960x640`, `1093x614` (`1366x768` at 125%), and `853x480` (`1280x720` at 150%), then verify search, product selection, table filtering, and export buttons are usable.

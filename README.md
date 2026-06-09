# 不具合情報検索

不具合情報の検索、集計確認、Excel 出力を行う Windows 向けデスクトップアプリです。

画面は `pywebview` + `Edge WebView2`、業務ロジックは service / repository 層で構成しています。現在の通常運用DBは PostgreSQL です。Access repository は切り戻し用に残しています。

## 構成

```text
defect_information_search/
├─ main.py
├─ build_exe.ps1
├─ requirements.txt
├─ .env.example
├─ database/
│  └─ postgresql/
│     ├─ 001_schema.sql
│     ├─ 002_indexes.sql
│     ├─ 003_constraints.sql
│     ├─ 010_import_from_csv.sql
│     ├─ 020_validation.sql
│     └─ migration_notes.md
├─ docs/
│  ├─ postgresql-migration.md
│  └─ 工業検査とエラー検出アイコン.png
├─ scripts/
│  ├─ migrate_access_to_postgres.py
│  ├─ adjust_postgres_sequences.py
│  └─ smoke_test_postgres_repository.py
└─ src/
   └─ defect_information_search/
      ├─ config.py
      ├─ domain/
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
POSTGRES_CONNECTION_URL=postgresql://ユーザー名:パスワード@192.168.1.120:5432/defect_information_search
POSTGRES_SCHEMA=public
```

- `DB_BACKEND=postgres`: PostgreSQL を使用します。
- `DB_BACKEND=access`: Access へ切り戻します。
- `.env` は認証情報を含むため、Git 管理しません。

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
.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('scripts/smoke_test_postgres_repository.py', run_name='__main__')"
```

## PostgreSQL 移行

移行は完了済みです。詳細は次を参照してください。

- `docs/postgresql-migration.md`
- `database/postgresql/migration_notes.md`

作業済み内容:

- Access 6テーブルを PostgreSQL へ投入
- PostgreSQL 英語物理名へ統一
- `PostgresDefectRepository` 実装
- `domain_mappers.py` 英語列名対応
- アプリ起動、検索、詳細表示、時間列表示、日付範囲検索、廃棄データ系、Excel 出力を確認

## ビルド

onefile の exe は次で作成します。

```powershell
.\build_exe.ps1
```

ビルドスクリプトは `docs\工業検査とエラー検出アイコン.png` から `.ico` を生成し、`.env` も同梱したうえで PyInstaller onefile を作成します。

最終成果物は `dist\不具合情報検索.exe` です。

## 配布時の前提

- 配布先 PC には Microsoft Edge WebView2 Runtime が必要です。
- PostgreSQL サーバー `192.168.1.120:5432` へ接続できる必要があります。
- 切り戻し運用を行う場合のみ、`.env` の `ACCESS_DB_PATH` へ到達できる必要があります。

## 主な機能

- 品番候補検索
- 候補一覧からの詳細表示
- 号機絞り込み
- 集計値・不具合内訳表示
- 表示中データの Excel 出力
- 日付範囲での全品番エクスポート
- 集計データ出力
- 廃棄データ出力

## 補足

- 旧 PySide6 画面は削除済みです。
- 画面の見た目と業務ロジックは維持し、UI は WebView 化しています。
- Access repository は切り戻し期間のために残しています。

## UI Design

- `DESIGN/DESIGN.md` is the primary UI reference for the WebView screen tokens, spacing, cards, tables, and buttons.
- This screen has no page menu, so the left sidebar is not used.
- The ARAI logo is placed in the title row and bundled from `src/defect_information_search/webview/assets/arai_logo.png`.
- The footer is rendered at the bottom of the WebView with the standard copyright text.

## Display Size Notes

- The distributed WebView window minimum size is `960x640`.
- On normal-height screens, the app keeps the fixed full-window layout and the product/detail tables scroll inside their panels.
- On short screens, including `1366x768`, `1280x720`, and Windows display scale `125%` / `150%` equivalent viewports, the app switches to document-level vertical scrolling so the search fields, tables, export buttons, and footer remain reachable.
- For low-height checks, confirm the product list and detail list still have their own scrollbars, then scroll the whole window to reach lower operation buttons.
- Recommended manual checks: start the app, resize the window to around `960x640`, `1093x614` (`1366x768` at 125%), and `853x480` (`1280x720` at 150%), then verify search, product selection, table filtering, and export buttons are usable.

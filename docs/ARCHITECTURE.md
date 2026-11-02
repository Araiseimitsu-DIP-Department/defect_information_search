# 現在の構造

2026-10-09のコード調査に基づくConfirmed。実運用環境の確認結果ではない。

## 目的とデータフロー

不具合情報を検索・集計しExcelへ出力するWindowsデスクトップアプリ。

`main.py` → `src/defect_information_search/app.py` → `webview/app.py` が起動経路。AppConfigでRepositoryを選択し、Service・ExportService・WebviewBridgeを組み立てる。

`webview/assets/app.js` → `window.pywebview.api` → `webview/bridge.py` → `services/defect_service.py` → Repository → DB の順で検索する。MapperがDB列をドメインモデルに変換し、Serviceが日本語列のDataFrameを作る。Bridgeは日付・NULL等をJSONへ変換する。Excel書込みはExportService。

独立したHTTP API・外部通知サービスは確認されない。JSから公開されるBridgeメソッドはbootstrap、search_products、load_product、filter_by_machine、export_current、export_all_defects、export_aggregate、export_disposal、close_app。

## ファイルの役割

| パス | 役割 |
| --- | --- |
| `src/defect_information_search/config.py` | 環境設定・接続先・アプリ識別情報・版番号 |
| `webview/app.py` | pywebview / Edge WebView2起動、Repository選択 |
| `webview/assets/` | HTML・vanilla CSS・JavaScript・ロゴ |
| `application/ports/defect_repository.py` | RepositoryのProtocol |
| `domain/models.py` | dataclassによるDB非依存モデル |
| `domain/schema.py` | Access由来のテーブル概念定義。現行PGスキーマ定義ではない |
| `infrastructure/access/`、`infrastructure/postgres/` | DB別SQLと取得 |
| `infrastructure/mappers/` | 日英列対応・型変換 |
| `infrastructure/access_gateway.py` | ODBC接続・セッション |
| `services/` | 検索結果・集計・Excel出力 |
| `models.py` | 不具合内訳の共通列定義 |
| `scripts/`、`database/postgresql/` | スモーク確認・旧単一DB移行資産 |
| `docs/*_db/`、`docs/arai_masters/` | DB別移行資料と副作用のある実行スクリプト |
| `tools/pyi_rth_fix_six.py` | PyInstaller実行時のsix互換補正 |

## 実行環境

Python、pywebview、Edge WebView2、pandas、openpyxl、psycopg、python-dotenv、PyInstaller、sixを使用。PostgreSQLの依存指定はrequirements.txt、Access用のpyodbcはrequirements-access.txtで追加する。調査時の.venvはPython 3.12.10。移行専用依存は [DATABASE](DATABASE.md) を参照。

画面は最大化起動、初期指定1600×1200、最小960×640。狭い・低い画面でスクロール条件を切替える。UI主参照は [DESIGN](DESIGN.md)。loggingは起動時に無効化される。

業務動作は [BUSINESS_RULES](BUSINESS_RULES.md)、DBと設定は [DATABASE](DATABASE.md)、起動・検証は [RELEASE](RELEASE.md)。旧資料との違いは [KNOWN_GAPS](KNOWN_GAPS.md) に記録する。

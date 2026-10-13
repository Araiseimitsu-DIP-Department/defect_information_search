# PostgreSQL運用向けビルドの最適化

2026-10-13。Access対応コードを保持して、既存のPyInstaller onefile/windowed方式を維持した。

## 調査と変更

| 対象 | 分類・扱い |
| --- | --- |
| pyodbc、Access Repository、access_gateway | Access専用。ソースを保持し、PGビルドから除外。Access RepositoryはAccess選択時だけ読み込む |
| pypyodbc | プロジェクトで利用なし。PGビルドの除外指定で将来の混入を防ぐ |
| win32com | アプリで直接利用なし、今回のexeにも含まれない。pywin32全体は除外しない |
| webview.platforms.win32、winforms、edgechromium、pythonnet/CLR関連 | Windows表示用。Access専用ではないため維持 |
| psycopg、psycopg_binary・libpq関連、pandas、openpyxl、dotenv、six | PG接続・共通処理・Excel・起動用。維持 |
| docs配下のpyodbc・psycopg2利用の移行スクリプト、xlwings利用のマスター作成 | 通常アプリの依存経路外。ソースを保持し、同梱対象を増やさない |
| .accdb/.mdb、Access ODBC/ACEドライバー、移行資料・設定 | 元から明示同梱なし。生成exeの検査でもAccess DBファイル・ドライバー不在を確認 |
| .envのACCESS_*、DATABASE_BACKEND | PG向け同梱コピーから除外。DB_BACKEND=postgresを保持し、元の.envは変更しない |

変更ファイル：build_exe.ps1、tools/build_support.py、requirements.txt、requirements-access.txt、src/defect_information_search/webview/app.py、src/defect_information_search/config.py、tests/test_build_profiles.py、.env.example、README.md、docs/ARCHITECTURE.md、docs/DATABASE.md、docs/RELEASE.md、docs/update.md、本資料。

Access Gateway・RepositoryのPythonコード、SQL、移行スクリプトは変更・削除していない。PG Repository・Service・Excel処理・画面資産にも変更なし。設定の探索順・互換キー・環境変数優先を維持する。Accessへ戻す手順は [RELEASE](RELEASE.md)。PG専用exeに設定だけでAccess機能を追加することはできない。

## 検証結果

- PASS：既存47件＋追加6件の全53件Tests。AccessパスなしのPG設定、Accessパス必須、同梱設定の除外・値保存、Accessプロファイル設定保存、Accessインポートを拒否した別Pythonプロセスでの画面起動経路、PG専用exeのAccess選択拒否を追加検証。画面作成・WebView開始は自動Testsではモック。
- PASS：実PGへdefault_transaction_read_only=onで接続し、既存smoke_test_postgres_repository.pyを実行。品番候補6件、対象品番明細23,723件、期間明細106,767件、QR対象27,253件、5ロットの明細5件、製品マスター1件、全件出力47列・先頭3行を確認。業務結果の以前との同値性まで証明する比較ではない。
- PASS：build_exe.ps1による生成と生成exeアーカイブ検査。Accessモジュール・pyodbc/pypyodbc・Access DB/ドライバーファイル・Access設定項目なし。PG・Excel・WebView Windowsモジュール、ICO、HTML/CSS/JS/ロゴを保持。
- PASS：生成exeを非表示で15秒起動し、子プロセスの継続と「不具合情報検索」ウィンドウ生成を確認。検証用プロセスは終了した。画面内の操作までは未確認。
- サイズ：37,481,604 → 37,413,664バイト。67,940バイト（約0.181%）減。共通依存を維持したため減少は小さい。旧成果物はGit対象外のruntime/build-backup/20261013へ保全。

最初のTests実行はサンドボックスの一時フォルダー制限で失敗し、許可された通常権限の再実行でPASS。PGスモークも制限下では接続失敗し、許可された通常権限でPASS。生成exeと認証情報を含む.envはGit・外部配布の対象にしていない。

## 未確認事項

実画面での検索・号機・期間操作と全Excel出力操作、別配布PCのWebView2・DB到達性、Access用exeの再ビルドと実Access接続は未実施。自動Tests・実PG参照・アーカイブ検査はそれぞれの範囲の確認であり、全機能の実機確認ではない。

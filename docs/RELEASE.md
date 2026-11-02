# 起動・検証・配布

## 現在の起動方法

依存指定はrequirements.txt。既存の仮想環境と.env.exampleを基に設定した環境で実行する。

```powershell
.\.venv\Scripts\python.exe main.py
```

設定の仕様は [DATABASE](DATABASE.md)。WindowsのEdge WebView2 Runtimeと利用DBへの到達性が必要。Access切り戻し時はAccess ODBCドライバーと指定パスへの到達性が必要。

## Verification Gate

変更に関係する検証を選び、PASS / FAIL / NOT RUN / 適用外と理由を報告する。文書だけの変更に実DB・exeビルドを一律に要求しない。

| 検証 | 実在する方法・適用範囲 |
| --- | --- |
| 自動Tests | `.\.venv\Scripts\python.exe -B -m unittest discover -v`。DBに接続せず、一時ファイルだけを扱う |
| 構文 | Pythonのast.parseで変更した.pyを解析。バイトコードを作らず確認可能 |
| lint・型チェック | 設定・正式コマンドは未整備。存在しない必須コマンドを追加しない |
| ハーネス | Markdown参照先、Skill frontmatter、Rules frontmatter、役割分離・重複・Unknown混入を確認 |
| 実DB参照 | `.\.venv\Scripts\python.exe scripts\smoke_test_postgres_repository.py`。本番を含み得る接続先と依頼範囲を先に確認 |
| 起動・機能 | main.pyまたは生成exeで検索、品番選択、号機、日付、各Excel出力、取消・空状態を確認 |
| UI変更 | 960×640、1093×614、853×480相当の表示で操作・スクロール到達性を確認。ネイティブ最小サイズより小さい値は表示倍率を含む論理ビューポートの目安 |
| ビルド | 下記のビルドが依頼範囲にある場合だけ実施 |
| Git | `git diff --check`、`git diff`、`git status --short`。未追跡ファイルはdiffに出ないので別途読む |

データ更新に関係する作業は [共通検証](../.agents/skills/development-workflow/references/data-update-verification.md) の必要項目も満たす。Tests成功で実DB・UI・データ移行の安全性まで確認済みとしない。必要検証が未確認またはCritical / Highが残る場合、無条件にRelease Readyとしない。

## ビルドの現在の動作

```powershell
.\build_exe.ps1
```

build_exe.ps1はプロジェクトルートからの実行を確認し、distとbuildを削除する。必要な旧成果物は実行前に保全する。docs/app_icon.pngからICOを作成し、設定・画面資産を同梱してPyInstaller onefile/windowedを生成する。最終成果物はdist/不具合情報検索.exe。成功時にspecとbuildを削除する。.envの認証情報が成果物内に含まれる。

既定の`-Backend postgres`はpyodbc・pypyodbc・Access Repository・Gatewayを除外し、同梱.envからACCESS_*と互換backendキーを除く。元の.envは変更しない。PostgreSQL運用ではACCESS_DB_PATHは不要。`build_backend.txt`を同梱し、PostgreSQL専用exeでAccessを選択すると接続前に停止する。外置き.envの探索順と環境変数優先は維持する。

Accessに戻す場合は`requirements-access.txt`をインストールし、`.env`をAccess用に設定して`.\build_exe.ps1 -Backend access`で再ビルドする。設定ファイルのbackendとビルド指定が一致しない場合は停止する。両プロファイルともPG依存は維持する。

PythonExe引数は従来どおり。PyInstallerや設定準備・成果物検査の失敗はエラーで停止する。生成exeのアーカイブを検査し、必要なPG・画面モジュールと資産、およびPGビルドのAccess依存不在を確認する。失敗時のbuildには診断資料・認証情報を含む設定が残り得る。成果物の存在だけで起動成功とは判断しない。調査・検証の詳細は [BUILD_OPTIMIZATION](BUILD_OPTIMIZATION.md)。

## 配布・復旧の確認事項

版番号は `config.py` の `APP_VERSION` だけを更新する。画面変更前が 1.0.0、候補検索と不具合表示の分離が 1.1.0。操作や出力の追加は minor、不具合修正は patch、検索・出力結果が変わる非互換は major。画面はフッター右に `v` 付きで表示する。履歴は [update](update.md) に版番号を記し、別の変更履歴は作らない。配布経路、対象PC、成果物の保管、リリース承認者、バックアップ・復旧手順はUnknown。現在のアプリコードが使うDBは3種類。READMEの4DB記載との差は [KNOWN_GAPS](KNOWN_GAPS.md) を参照する。

Access切り戻しの設定例は [postgresql-migration](postgresql-migration.md)。DB間の結果同等性は未検証。設定切替はDB移行のロールバックではない。

本番反映の承認条件は [safety.mdc](../.cursor/rules/safety.mdc)。リリースの進め方は [release](../.agents/skills/release/SKILL.md)。変更履歴は [update](update.md) とし、別のCHANGELOGを重複作成しない。

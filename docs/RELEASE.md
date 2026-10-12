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

build_exe.ps1はカレントをプロジェクトルートとしてdistとbuildを削除し、docs/app_icon.pngからICOを作成、.env・画面資産を同梱してPyInstaller onefile/windowedを生成する。最終成果物はdist/不具合情報検索.exe。終了時にspecとbuildを削除する。.envの認証情報が成果物内に含まれる。

スクリプトはPythonExe引数を受け取る。PyInstallerの失敗がPowerShellの終了コードへ確実に伝わるかは未検証。成果物の存在だけで起動成功とは判断しない。

## 配布・復旧の確認事項

正式バージョンの付け方、配布経路、対象PC、成果物の保管、リリース承認者、バックアップ・復旧手順はUnknown。現在のアプリコードが使うDBは3種類。READMEの4DB記載との差は [KNOWN_GAPS](KNOWN_GAPS.md) を参照する。

Access切り戻しの設定例は [postgresql-migration](postgresql-migration.md)。DB間の結果同等性は未検証。設定切替はDB移行のロールバックではない。

本番反映の承認条件は [safety.mdc](../.cursor/rules/safety.mdc)。リリースの進め方は [release](../.agents/skills/release/SKILL.md)。変更履歴は [update](update.md) とし、別のCHANGELOGを重複作成しない。

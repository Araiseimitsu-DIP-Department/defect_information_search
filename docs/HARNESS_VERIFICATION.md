# ハーネス導入の検証記録

2026-10-09。対象はAIハーネスの設計・生成と、既存重要動作の確認Tests追加。

## Verification結果

| 項目 | 結果・範囲 |
| --- | --- |
| ユニットTests | PASS。既存24件と追加9件の全33件。DBに接続しない。サンドボックスの一時フォルダ制限を避けた環境で実行 |
| Python構文 | PASS。main・src・scripts・tests・docsの42ファイルをast.parseで解析 |
| Skill形式 | PASS。skill-creatorのquick_validate.pyのvalidate_skillで7 Skillsを検証 |
| 参照先 | PASS。追加ハーネスのローカルMarkdown参照先の存在を確認 |
| Rules形式 | PASS。2ファイルのdescriptionとalwaysApply=trueを確認 |
| 共通資料 | PASS。テンプレートの2参照資料とSHA-256が一致 |
| lint / 型チェック | NOT RUN。プロジェクトに正式な設定・コマンドが未整備 |
| 実DB・起動・UI | NOT RUN。今回の変更は文書・Rules・Skills・Tests。アプリコード変更なし。本番データを扱う必要がない |
| exeビルド・配布 | NOT RUN。アプリコード変更なし。既存成果物の削除と認証情報同梱を伴うビルド・本番配布は今回の範囲に含めない |
| Git差分 | CHECKED。既存追跡ファイルの変更なし。新規ファイルを個別確認し、git diff --checkも確認 |

Skill検証のPyYAMLはGit対象外のruntime内に検証用として配置した。アプリのrequirements.txt・既存仮想環境への依存追加は行っていない。

## データ更新検証の適用

追加Testは匿名の一時Excelを生成し、保存後の列・値・日付・NULL・書式をopenpyxlで読み戻した。同一保存先への再保存で古い行が残らないこと、別のファイルが保持されること、0件保存時のヘッダーだけのファイルを確認した。

Excelの途中停止、ファイルロック、UI取消・上書き確認、巨大データは未確認。DB更新・移行・復旧・再実行は今回実行していない。これらを成功とする評価は行わない。

## 自己レビュー

- AGENTSは地図、Rulesは常時制約、Skillsは手順、Docsは仕様・調査記録、Testsは観測結果、updateは履歴という役割を確認した。
- 業務仕様をSkillsへコピーせず、DBの詳細列対応・UIトークンは既存Docsを参照した。Verification GateはRELEASE、Approval Gateはsafety.mdcへ集約した。
- Domain SkillsはDB境界と集計・帳票の2領域に限定した。共通手順をdevelopment-workflowのreferencesに置き、関連Skillsから条件付きで参照した。
- Confirmedはコードで確認できた動作として記録し、業務承認済みとは扱っていない。Assumption / Unknownと資料矛盾はKNOWN_GAPSに残した。
- Testsでは集計不良率、切粉除外・P条件・金額条件、集計と廃棄の差、Excel列と書式位置の整合を確認した。未確定な単位・丸めの期待値は追加していない。
- 既存Testsの期待値、アプリコード、.env、requirements.txt、移行スクリプト、既存業務資料を変更していない。
- 本番操作を暗黙に許可する手順を作らず、今後の学びは具体案への承認後に反映する形にした。

今回の範囲で未解決のCritical / High指摘はない。ハーネス導入は完了。アプリのRelease Readyは判定していない。残る業務・運用確認は [KNOWN_GAPS](KNOWN_GAPS.md) に集約する。

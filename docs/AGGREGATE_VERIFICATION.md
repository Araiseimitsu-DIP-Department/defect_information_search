# 検査日基準の集計出力：実装・検証記録

2026-10-12。変更対象は「集計データ」のみ。確定仕様は [BUSINESS_RULES](BUSINESS_RULES.md)。

## 実装範囲

| ファイル・領域 | 役割 |
| --- | --- |
| services/aggregate_service.py | 期内初回の検査・先頭不具合採用、切粉差引き、円丸め配分、確認件数 |
| services/defect_service.py | 集計だけ専用処理へ委譲。他の出力は従来処理 |
| domain/models.py、application/ports/defect_repository.py、infrastructure/mappers/domain_mappers.py | 検査集計モデル・集計専用Repository契約・列変換 |
| infrastructure/postgres/defect_repository.py | 通常・保存の検査記録、ID順の不具合情報の取得 |
| infrastructure/access/defect_repository.py、config.py、webview/app.py、.env.example | Access集計専用取得と任意の外観検査DBパス |
| services/export_service.py | 検査日追加後の列名による書式、集計条件シート |
| webview/bridge.py、assets/app.js、assets/index.html | 検査日基準の操作表示、保存時の確認件数 |
| tests/ | 期・月境界、保存分、重複、切粉、円丸め、取得SQL、取消・エラー、Excel読戻し |
| README、BUSINESS_RULES、DATABASE、KNOWN_GAPS、update | 現行仕様と変更履歴 |

検索・表示中明細・全品番・廃棄の抽出条件は変更していない。別プロジェクトは参照のみで、書込みなし。.envの実値や本番DBの変更は行っていない。

## 検証結果

- 自動Tests：全47件PASS。追加14件と、既存の集計・Excelテストの仕様更新を含む。
- Python構文、JavaScriptのnode --check、git diff --check：PASS。
- 実PostgreSQL：通常・保存・不具合・マスターを読み取り専用トランザクションで取得。集計結果を別プロジェクトの未変更の計算関数へP条件・切粉差引きを適用した結果とロット・日付・金額単位で照合し一致。
- 各期の12か月の出力金額合計が期全体の金額と一致。
- 一時Excelへ保存し、行数・金額合計・集計条件シートをopenpyxlで読み戻して一致。検証用Excelは一時領域で処理。

| 期 | 出力行数 | 廃棄金額（現在単価の参考値） |
| --- | ---: | ---: |
| 41期 | 9,209 | 14,204,107円 |
| 42期 | 6,198 | 9,134,228円 |

確認した検査記録の範囲は2024/10/1～2026/6/25。42期は期末までのデータが揃っているという評価ではない。DBの同期・記録状態が変われば結果も変わる。

## データ更新検証・レビュー

DBはSELECTのみ。ファイル書込みは匿名データの回帰Testsと一時的な実データExcel読戻しで確認。保存取消で検索・書込みしないこと、取得失敗時に既存ファイルが保持されること、正常保存・再保存・他ファイル保持を確認した。

列追加で書式位置がずれないよう列名で指定した。抽出を月単位で先に絞って初回を選び直すことはせず、期全体の初回採用後に指定期間へ絞る。未照合・単価未登録を0件成功のように隠さず、保存時と集計条件シートで示す。検査日の存在しない記録を指示日で補わない。

Critical / Highの未解決指摘は今回のレビューでなし。既存の直接保存方式は維持し、ファイルロック・保存途中停止時の原子的置換は保証していない。

## 未実施

実Windows画面での検索・保存操作、Accessの期全体の結果照合は未実施。lint・型チェックの正式設定は未整備。アプリの本番リリース可否を無条件に判定していない。

## PostgreSQL切替後の再ビルド確認

ユーザーの.env変更後、実効backend=postgresを確認。読み取り専用で3DBへ接続し、品番検索4候補・明細1,827行、42期集計6,198行・9,134,228円、一時Excel読戻しを再確認した。検査記録の最大日は2026/6/25のまま。

全47件の回帰Tests、ハーネス形式・参照先、Python構文、JavaScript構文、Git差分を再確認。build_exe.ps1でonefile exeを再生成し、37,481,604バイトの成果物が生成された。内蔵の新集計モジュール・画面資産と、現在の.envとの同梱一致を確認した。非表示起動で15秒間プロセスが継続することを確認し、検証用プロセスを終了した。これは画面内の全操作の実機検証ではない。

旧exeはGit対象外のruntime/build-backupへ保全。.env・exe・検証用ファイルをコミット対象に含めず、コード・Docs・Rules・Skills・Testsを対象とする。外部配布・DB更新は行っていない。

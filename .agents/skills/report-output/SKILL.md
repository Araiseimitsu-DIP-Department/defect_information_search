---
name: report-output
description: 不具合情報検索の集計・廃棄データ・Excel出力を変更または検証するときに使う。
---

# 集計・帳票確認

仕様は docs/BUSINESS_RULES.md、Test対応と未確定事項は docs/KNOWN_GAPS.md。

1. 表示中明細、全品番、集計、廃棄のどの出力かを特定する。日付の基準と絞込み対象、列順、欠損、単重・単価の扱いを確認する。
2. 代表データで出力対象と除外対象、廃棄数・量・金額、集計不良率を手計算し、Service結果と照合する。業務上の理由・単位・丸めはUnknownを推測で埋めない。
3. tests/test_defect_service.py、test_report_business_rules.py、test_export_service.pyを中心に関連Testsを使う。DB条件変更ならdatabase-operationsを併用する。
4. Excel書込みの変更は [共通検証](../development-workflow/references/data-update-verification.md) のファイル関連項目を適用する。匿名の一時出力をopenpyxlで読み戻し、値・列・書式と対象外データ保持を確認する。
5. 保存取消、空データ、上書き、書込み失敗、部分ファイル、再実行の必要な検証を選ぶ。未実施は明示する。画面のフィルターと実際の出力行が一致するか対象操作で確認する。

本Skillは計算と帳票内容を担当する。DB移行・接続設定はdatabase-operations、レビュー全体はreview-codeに委ねる。

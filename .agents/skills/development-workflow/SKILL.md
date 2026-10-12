---
name: development-workflow
description: 不具合情報検索の機能追加・修正・レビュー・リリース準備で作業手順と検証を選ぶ。
---

# 作業の入口

1. AGENTS.md、両Rules、依頼に関係するDocsとTestsを読み、要求・影響範囲を整理する。資料矛盾・Unknownは docs/KNOWN_GAPS.md と照合する。
2. 追加・既存動作変更は [implement-feature](../implement-feature/SKILL.md)、不具合は [fix-bug](../fix-bug/SKILL.md)、レビューのみは [review-code](../review-code/SKILL.md)、配布準備は [release](../release/SKILL.md) を選ぶ。文書変更は必要な手順だけ使う。
3. DB切替・SQL・移行なら [database-operations](../database-operations/SKILL.md)、集計・廃棄・Excelなら [report-output](../report-output/SKILL.md) を併用する。
4. データ書込み機能の追加・変更時は [共通検証](references/data-update-verification.md) の該当項目を適用する。表示だけの変更には適用しない。
5. 実装後はレビューし、docs/RELEASE.md のVerification Gateを変更範囲に応じて満たす。対応するDocsと重要な変更のdocs/update.mdを更新する。
6. 再利用できる学びが判明したら [提案・承認・反映](references/learning-feedback.md) に従い具体案を提案する。今回の依頼を優先する。

完了報告には変更内容・ファイル、検証結果、Docs更新、未確認事項を含める。機能変更の依頼がない場合、ハーネス整備を理由に機能追加を開始しない。

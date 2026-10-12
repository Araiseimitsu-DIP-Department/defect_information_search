---
name: review-code
description: 不具合情報検索の変更を要求・既存仕様・テストと照合してレビューする。
---

# 変更レビュー

1. 要求、git diff、関連Docs・Testsを照合する。読み取りのみのレビュー依頼では勝手に修正しない。
2. 変更に応じて日付境界、空・NULL、型変換、数量0、集計の分母、JOINによる行増加、日英列対応、例外表示を確認する。DB・帳票の詳細は該当Domain Skillを使う。
3. 更新処理なら [共通検証](../development-workflow/references/data-update-verification.md) で対象判定、部分commit、再実行、読み戻し、対象外データ保持を評価する。
4. 根拠と再現条件を伴う指摘をCritical / High / Medium / Lowに分類する。仕様不明と実装不具合を区別する。Critical / Highが残る場合はリリース可能と判定しない。
5. DocsとTestsの整合、不要な変更、Verification・Approval Gateの適用を確認する。
6. 実証された確認漏れは [学びの提案手順](../development-workflow/references/learning-feedback.md) で具体化する。

指摘がない場合も確認範囲と未確認事項を報告する。

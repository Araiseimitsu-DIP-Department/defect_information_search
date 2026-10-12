---
name: fix-bug
description: 不具合情報検索の異常動作を再現・原因調査し、最小修正と回帰検証を行う。
---

# 不具合対応

1. 現象・発生条件・期待結果を整理し、関連Docs・Testsを読む。
2. 再現する。再現できない場合は候補と未確認事項を区別し、推測だけで修正しない。
3. 関連コード・利用可能なログ・データ経路を追い、根本原因と影響を整理する。本番データの修正を再現手段にしない。
4. 最小修正を行い、実証した発生経路を回帰Testに残す。業務仕様が不明な部分はHuman Validation Requiredとする。
5. 書込み処理なら [共通検証](../development-workflow/references/data-update-verification.md) で途中停止・再実行・読み戻しを確認する。
6. 再現確認と関連回帰Tests、[review-code](../review-code/SKILL.md)、docs/RELEASE.md のVerification Gate、必要なDocs・履歴更新を実施する。
7. 確定した原因・確認漏れから再利用可能な学びがあれば [提案手順](../development-workflow/references/learning-feedback.md) を使う。

原因、修正、変更ファイル、検証、影響、残るリスクを報告する。

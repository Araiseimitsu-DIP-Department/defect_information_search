---
name: implement-feature
description: 不具合情報検索に機能を追加する、または既存動作を意図的に変更するときに使う。
---

# 機能追加・変更

1. 要求を観測可能な結果として整理し、AGENTS.mdから関連Docs・Tests・Domain Skillを確認する。
2. 画面→Bridge→Service→Repository→Mapperの影響範囲を追う。業務判断が不明な点だけをHuman Validation Requiredとし、独立して進められる作業を進める。
3. 既存構造で最小限に実装する。既存の重要動作と新しい要求を確かめるTestsを選び、必要なら追加する。
4. DB・Excelなど書込みに関係する場合は [共通検証](../development-workflow/references/data-update-verification.md) を適用する。
5. [review-code](../review-code/SKILL.md) と docs/RELEASE.md のVerification Gateを実施し、必要なDocs・履歴を更新する。
6. 再利用できる学びは [学びの手順](../development-workflow/references/learning-feedback.md) に従い提案する。

追加機能、変更ファイル、テスト、Docs、残る制約を報告する。

---
name: release
description: 不具合情報検索のexeビルド・配布前検証・リリース準備を行う。
---

# リリース準備

1. docs/RELEASE.mdとRulesを読み、要求範囲、変更内容、バージョンの扱い、配布先、復旧方法を確認する。未定の運用ルールを作らない。
2. 関連Tests、[review-code](../review-code/SKILL.md)、README、.env.example、関連Docs、docs/update.md、git diff / statusを確認する。
3. データ更新を伴うリリースだけ [共通検証](../development-workflow/references/data-update-verification.md) を適用する。
4. ビルドが依頼範囲にある場合はbuild_exe.ps1の削除対象と.env同梱を確認し、必要な成果物を保全して実行する。ビルド失敗時は成功した成果物として扱わない。
5. 生成exeについて起動・対象操作・WebView2・DB到達性を配布対象環境で検証する。ビルド成功と機能確認を区別する。
6. 配布・本番反映はApproval Gateと既存のユーザー許可を確認して実行する。

Tests、起動、対象機能、ビルド、Git、未確認事項とリリース可否を報告する。再利用できる学びは [提案手順](../development-workflow/references/learning-feedback.md) に従う。

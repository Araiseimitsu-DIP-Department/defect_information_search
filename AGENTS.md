# 不具合情報検索：開発ガイド

Windows向けの不具合検索・集計・Excel出力アプリ。入口は `main.py`、画面は pywebview / Edge WebView2。

## 最初に見る場所

- 常時制約：[開発ルール](.cursor/rules/development.mdc)、[安全ルール](.cursor/rules/safety.mdc)。Codexでも両方を読む。
- 構造：[ARCHITECTURE](docs/ARCHITECTURE.md)、業務動作：[BUSINESS_RULES](docs/BUSINESS_RULES.md)。
- DB・更新処理：[DATABASE](docs/DATABASE.md)。詳細な現行列対応は [PostgreSQL運用資料](docs/postgresql-migration.md)。
- 起動・検証・配布：[RELEASE](docs/RELEASE.md)。未確定事項・資料矛盾：[KNOWN_GAPS](docs/KNOWN_GAPS.md)。
- UIの主参照は [docs/DESIGN.md](docs/DESIGN.md)。変更履歴は [update](docs/update.md)。
- ハーネスの設計は [HARNESS_DESIGN](docs/HARNESS_DESIGN.md)、導入時の検証記録は [HARNESS_VERIFICATION](docs/HARNESS_VERIFICATION.md)。

## 作業の選択

まず [development-workflow](.agents/skills/development-workflow/SKILL.md) で必要な手順を選ぶ。

- 機能追加：[implement-feature](.agents/skills/implement-feature/SKILL.md)
- 不具合修正：[fix-bug](.agents/skills/fix-bug/SKILL.md)
- レビュー：[review-code](.agents/skills/review-code/SKILL.md)
- リリース準備：[release](.agents/skills/release/SKILL.md)
- DB切替・列対応・移行：[database-operations](.agents/skills/database-operations/SKILL.md)
- 集計・廃棄・Excel：[report-output](.agents/skills/report-output/SKILL.md)

データを書き込む機能の変更時だけ [データ更新の共通検証](.agents/skills/development-workflow/references/data-update-verification.md) を適用する。再利用できる学びが判明したら [提案・承認・反映手順](.agents/skills/development-workflow/references/learning-feedback.md) を使う。

検証範囲と未実施理由を日本語で報告する。承認条件と実行可能な検証方法は上記Rules・RELEASEを参照する。

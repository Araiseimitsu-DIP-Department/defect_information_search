# ハーネス設計と実装範囲

## 設計判断

既存アプリの動作は変更せず、2026-10-09の調査で確認できた仕様と不一致を分離する。ユーザーの「最後まで対応」の依頼に基づきPhase 2の設計からPhase 3の生成まで実施する。通常開発は手順を整備する範囲で、未依頼の機能追加・本番配布を含めない。

| 配置 | 役割 |
| --- | --- |
| AGENTS.md | 参照先とSkill選択の地図 |
| .cursor/rules/ | 常時制約・Approval Gate。CodexはAGENTS経由で参照 |
| .agents/skills/ | 作業手順と条件付きの共通検証 |
| docs/ARCHITECTURE.md | 現在の構造・技術・データフロー |
| docs/BUSINESS_RULES.md | 実装から確認した業務動作 |
| docs/DATABASE.md | 設定・DB境界・更新資産の性質 |
| docs/RELEASE.md | 実在する起動・検証・ビルド方法と未確定な配布事項 |
| docs/KNOWN_GAPS.md | Assumption / Unknown・資料矛盾・仕様Test対応 |
| tests/ | 既存Testsに加え、重要な集計条件とExcel読戻しの確認 |
| docs/update.md | 変更履歴のみ |

独立HTTP APIがないためAPI.mdは作らず、ローカルBridgeの関係はARCHITECTUREへ記載する。詳細なDB列対応・UIトークンは既存資料へ参照し重複させない。旧資料の矛盾は勝手に修正せずKNOWN_GAPSへ集約する。

## Skillの役割

すべてのSkillはAGENTS・Rulesを前提に、必要な資料だけを読む。

| Skill | 使用タイミング・目的 | 主なDocs | 関連Tests・他Skillとの差 |
| --- | --- | --- | --- |
| development-workflow | 開発依頼を分類し手順を選択 | HARNESS_DESIGN、RELEASE、KNOWN_GAPS | 変更範囲で選択。実装手順を重複させない |
| implement-feature | 機能追加・意図的な動作変更 | 対象仕様・構造 | 要求に対応するTests。不具合再現とは区別 |
| fix-bug | 再現から最小修正・回帰確認 | 対象仕様・KNOWN_GAPS | 発生経路の回帰Tests。推測修正を避ける |
| review-code | 要求・仕様・変更の照合 | 対象仕様・RELEASE | 関連Testsの有効性。実装・配布とは別 |
| release | exe・配布前準備 | RELEASE、DATABASE | 関連全Testsと実機確認。配布許可を内包しない |
| database-operations | DB切替・SQL・列対応・移行 | DATABASE、postgresql-migration、KNOWN_GAPS | config、両Repository SQL、Mapper Tests。DB境界を担当 |
| report-output | 集計・廃棄・Excel確認 | BUSINESS_RULES、KNOWN_GAPS | Service、業務条件、Excel Tests。計算と帳票を担当 |

Domain SkillはDB境界と帳票の2つに限定する。手順の重複を避け、検査員専用・品番検索専用など細分化したSkillは追加しない。

データ更新と学びの共通手順はtemplatesのcreate-harness/referencesからdevelopment-workflow/referencesへ配置する。参照条件はAGENTSと関連Skillsで明記する。

## 検証・承認の設計

Verification Gateの原本はRELEASE、Approval Gateの原本はsafety.mdc。新たな本番操作・依存追加・デプロイをハーネス生成から暗黙に許可しない。学びの具体案はユーザー承認後に反映する。

ハーネス整備の完了とアプリのリリース準備完了を分ける。本番・実DB・UI・exe未検証は制約として報告する。

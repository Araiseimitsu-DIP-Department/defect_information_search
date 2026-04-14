from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TableDefinition:
    table_name: str
    concept_name: str
    primary_key: str | None
    note: str


TABLE_DEFINITIONS = {
    "qr_history": TableDefinition(
        table_name="t_QR履歴",
        concept_name="QR履歴",
        primary_key=None,
        note="ロットの工程実績と日付時点の数量を保持する。",
    ),
    "defect_information": TableDefinition(
        table_name="t_不具合情報",
        concept_name="不具合実績",
        primary_key="ID",
        note="ロット単位の不具合件数と内容を保持する。",
    ),
    "inspector_master": TableDefinition(
        table_name="t_数値検査員マスタ",
        concept_name="検査員マスタ",
        primary_key="検査員ID",
        note="検査員コードの参照マスタ。",
    ),
    "inspection_record": TableDefinition(
        table_name="t_数値検査記録",
        concept_name="検査記録",
        primary_key="ID",
        note="数値検査の実績記録。",
    ),
    "product_catalog": TableDefinition(
        table_name="t_現品票検索用",
        concept_name="現品票検索用",
        primary_key=None,
        note="品番検索とロット表示に使う参照ビュー相当。",
    ),
    "product_master": TableDefinition(
        table_name="t_製品マスタ",
        concept_name="製品マスタ",
        primary_key="製品番号",
        note="製品属性・単価・材質などの参照マスタ。",
    ),
}


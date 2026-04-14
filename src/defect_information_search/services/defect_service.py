from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from defect_information_search.application.ports.defect_repository import DefectRepository
from defect_information_search.domain.models import DefectRecord, ProductCatalogItem
from defect_information_search.infrastructure.mappers.domain_mappers import (
    defect_records_frame_from_items,
    defect_records_from_frame,
    product_catalog_frame_from_items,
    product_master_frame_from_items,
    qr_history_frame_from_items,
)
from defect_information_search.models import DEFECT_FIELDS
from defect_information_search.services.export_service import ExportService


DETAIL_COLUMNS = [
    "ID",
    "生産ロットID",
    "品番",
    "指示日",
    "号機",
    "検査者1",
    "検査者2",
    "検査者3",
    "検査者4",
    "検査者5",
    "時間",
    "数量",
    "総不具合数",
    "不良率",
    "外観キズ",
    "圧痕",
    "切粉",
    "毟れ",
    "穴大",
    "穴小",
    "穴キズ",
    "バリ",
    "短寸",
    "面粗",
    "サビ",
    "ボケ",
    "挽目",
    "汚れ",
    "メッキ",
    "落下",
    "フクレ",
    "ツブレ",
    "ボッチ",
    "段差",
    "バレル石",
    "径プラス",
    "径マイナス",
    "ゲージ",
    "異物混入",
    "形状不良",
    "こすれ",
    "変色シミ",
    "材料キズ",
    "ゴミ",
    "その他",
    "その他内容",
    "数値検査員",
]

PRODUCT_CATALOG_COLUMNS = ["品番", "品名", "客先"]


@dataclass
class SearchResult:
    all_details: pd.DataFrame
    summary: dict[str, Any]
    details: pd.DataFrame
    machines: list[str]


class DefectService:
    def __init__(self, repository: DefectRepository) -> None:
        self.repository = repository

    def find_products(self, keyword: str) -> pd.DataFrame:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return pd.DataFrame(columns=PRODUCT_CATALOG_COLUMNS)
        products = list(self.repository.find_products(normalized_keyword))
        return self._products_to_frame(products)

    def load_search_result(
        self,
        part_number: str,
        date_from: date,
        date_to: date,
        machine: str | None,
    ) -> SearchResult:
        defect_records = list(self.repository.find_defects_for_part(part_number, date_from, date_to))
        all_details = defect_records_frame_from_items(defect_records)
        return self.build_search_result(all_details, machine)

    def build_search_result(self, all_details: pd.DataFrame, machine: str | None) -> SearchResult:
        if all_details.empty:
            return SearchResult(all_details=all_details, summary={}, details=all_details, machines=["全て"])

        machines = self._machine_values_from_details(all_details)
        details = self._filter_details_by_machine(all_details, machine)
        details = self._prepare_detail_frame(details)
        summary = self._build_summary_from_details(details)
        return SearchResult(
            all_details=all_details,
            summary=summary,
            details=details,
            machines=["全て", *machines] if machines else ["全て"],
        )

    def export_all_defects_to_excel(
        self,
        export_service: ExportService,
        target_path: Path,
        date_from: date,
        date_to: date,
    ) -> int:
        columns, rows = self.repository.iter_all_defects(date_from, date_to)
        return export_service.export_rows(columns, rows, target_path)

    def export_aggregate(self, date_from: date, date_to: date) -> pd.DataFrame:
        defects = defect_records_frame_from_items(list(self.repository.find_defects_between(date_from, date_to)))
        if defects.empty:
            return defects

        defects["廃棄不具合数"] = defects["総不具合数"].fillna(0) - defects["切粉"].fillna(0)
        defects = defects[
            (defects["廃棄不具合数"] > 0)
            & defects["生産ロットID"].fillna("").astype(str).str.startswith("P")
        ].copy()
        if defects.empty:
            return defects

        master = product_master_frame_from_items(
            list(self.repository.find_product_master_for_parts(defects["品番"].dropna().astype(str).tolist()))
        )
        merged = defects.merge(master, left_on="品番", right_on="製品番号", how="left")
        merged["単価"] = pd.to_numeric(merged["単価"], errors="coerce")
        merged["製品単重"] = pd.to_numeric(merged["製品単重"], errors="coerce")
        merged["廃棄量"] = merged["廃棄不具合数"] * merged["製品単重"]
        merged["廃棄金額"] = merged["廃棄不具合数"] * merged["単価"]
        merged = merged[merged["廃棄金額"].fillna(0) > 0].copy()
        if merged.empty:
            return merged

        columns = [
            "生産ロットID",
            "品番",
            "指示日",
            "号機",
            "検査者1",
            "検査者2",
            "検査者3",
            "検査者4",
            "検査者5",
            "時間",
            "数量",
            "製品単重",
            "材質",
            "単価",
            "廃棄量",
            "廃棄金額",
            "廃棄不具合数",
            "総不具合数",
            "不良率",
        ] + [label for label, _ in DEFECT_FIELDS] + ["その他内容"]
        return self._ensure_columns(merged, columns).sort_values(["品番", "指示日"]).reset_index(drop=True)

    def export_disposal(self, date_from: date, date_to: date) -> pd.DataFrame:
        qr_lots = qr_history_frame_from_items(list(self.repository.find_qr_history_lots(date_from, date_to)))
        if qr_lots.empty:
            return pd.DataFrame()

        defects = defect_records_frame_from_items(
            list(self.repository.find_defects_for_lots(qr_lots["生産ロットID"].dropna().astype(str).tolist()))
        )
        if defects.empty:
            return pd.DataFrame()

        defects["廃棄数"] = defects["総不具合数"].fillna(0) - defects["切粉"].fillna(0)
        defects = defects[
            (defects["廃棄数"] > 0)
            & defects["生産ロットID"].fillna("").astype(str).str.startswith("P")
        ].copy()
        if defects.empty:
            return pd.DataFrame()

        master = product_master_frame_from_items(
            list(self.repository.find_product_master_for_parts(defects["品番"].dropna().astype(str).tolist()))
        )
        merged = defects.merge(qr_lots, on="生産ロットID", how="inner")
        merged = merged.merge(master, left_on="品番", right_on="製品番号", how="left")
        merged["製品単重"] = pd.to_numeric(merged["製品単重"], errors="coerce")
        merged["単価"] = pd.to_numeric(merged["単価"], errors="coerce")
        merged["廃棄量"] = merged["廃棄数"] * merged["製品単重"]
        merged["廃棄金額"] = merged["廃棄数"] * merged["単価"]

        columns = [
            "品番",
            "生産ロットID",
            "廃棄数",
            "製品単重",
            "廃棄量",
            "材料識別",
            "単価",
            "廃棄金額",
            "客先名",
        ]
        return self._ensure_columns(merged, columns).drop_duplicates().sort_values(
            ["品番", "生産ロットID"]
        ).reset_index(drop=True)

    def _build_summary_from_details(self, details: pd.DataFrame) -> dict[str, Any]:
        if details.empty:
            return {}

        defect_records = defect_records_from_frame(details)
        quantity = sum(record.quantity or 0 for record in defect_records)
        defect_count = sum(record.total_defects or 0 for record in defect_records)
        summary = {
            "quantity": int(quantity),
            "defect_count": int(defect_count),
            "defect_rate": (float(defect_count) / float(quantity)) if quantity else None,
        }
        for label, _ in DEFECT_FIELDS:
            value = sum(record.defect_counts.get(label, 0) for record in defect_records)
            summary[label] = int(value) if value else None
        return summary

    def _machine_values_from_details(self, details: pd.DataFrame) -> list[str]:
        if "号機" not in details.columns:
            return []
        machines = details["号機"].dropna().astype(str).map(str.strip)
        return sorted({machine for machine in machines if machine})

    def _filter_details_by_machine(self, details: pd.DataFrame, machine: str | None) -> pd.DataFrame:
        if not machine or "号機" not in details.columns:
            return details.copy()
        filtered = details[details["号機"].fillna("").astype(str) == machine]
        return filtered.reset_index(drop=True)

    def _prepare_detail_frame(self, details: pd.DataFrame) -> pd.DataFrame:
        prepared = self._ensure_columns(details.copy(), DETAIL_COLUMNS)
        prepared["数値検査員"] = None
        return prepared.loc[:, DETAIL_COLUMNS].reset_index(drop=True)

    def _ensure_columns(self, dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        normalized = dataframe.copy()
        for column in columns:
            if column not in normalized.columns:
                normalized[column] = None
        return normalized.loc[:, columns]

    def _products_to_frame(self, products: list[ProductCatalogItem]) -> pd.DataFrame:
        frame = product_catalog_frame_from_items(products)
        return self._ensure_columns(frame, PRODUCT_CATALOG_COLUMNS).reset_index(drop=True)

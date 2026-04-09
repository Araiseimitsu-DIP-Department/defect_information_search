from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from defect_information_search.infrastructure.access_gateway import AccessGateway, AccessSession
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

SOURCE_DEFECT_COLUMNS = [column for column in DETAIL_COLUMNS if column != "数値検査員"]
PRODUCT_CATALOG_COLUMNS = ["品番", "品名", "客先"]
PRODUCT_MASTER_COLUMNS = ["製品番号", "製品単重", "材質", "単価", "材料識別", "客先名"]
DISPOSAL_DEFECT_COLUMNS = ["品番", "生産ロットID", "総不具合数", "切粉"]


@dataclass
class SearchResult:
    all_details: pd.DataFrame
    summary: dict[str, Any]
    details: pd.DataFrame
    machines: list[str]


class DefectService:
    def __init__(self, gateway: AccessGateway) -> None:
        self.gateway = gateway
        self._product_master_cache: dict[str, dict[str, Any]] = {}

    def find_products(self, keyword: str) -> pd.DataFrame:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return pd.DataFrame(columns=PRODUCT_CATALOG_COLUMNS)
        pattern = f"%{normalized_keyword}%"
        sql = """
            SELECT DISTINCT 品番, 品名, 客先
            FROM t_現品票検索用
            WHERE 品番 LIKE ?
               OR 品名 LIKE ?
               OR 客先 LIKE ?
            ORDER BY 品番
        """
        products = self.gateway.fetch_dataframe(sql, [pattern, pattern, pattern])
        return self._ensure_columns(products, PRODUCT_CATALOG_COLUMNS).reset_index(drop=True)

    def load_search_result(
        self,
        part_number: str,
        date_from: date,
        date_to: date,
        machine: str | None,
    ) -> SearchResult:
        with self.gateway.session() as session:
            all_details = self._defects_for_part(session, part_number, date_from, date_to)
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
        sql = f"""
            SELECT {self._select_clause(SOURCE_DEFECT_COLUMNS)}
            FROM t_不具合情報
            WHERE 指示日 BETWEEN ? AND ?
            ORDER BY 品番, 指示日, ID
        """
        with self.gateway.stream_rows(sql, [date_from, date_to]) as stream:
            return export_service.export_rows(stream.columns, stream, target_path)

    def export_aggregate(self, date_from: date, date_to: date) -> pd.DataFrame:
        with self.gateway.session() as session:
            defects = self._defects_between(session, date_from, date_to)
            if defects.empty:
                return defects

            defects["廃棄不具合数"] = defects["総不具合数"].fillna(0) - defects["切粉"].fillna(0)
            defects = defects[
                (defects["廃棄不具合数"] > 0)
                & defects["生産ロットID"].fillna("").astype(str).str.startswith("P")
            ].copy()
            if defects.empty:
                return defects

            master = self._product_master_for_parts(session, defects["品番"].dropna().astype(str).tolist())
            merged = defects.merge(master, left_on="品番", right_on="製品番号", how="left")
            merged["単価"] = pd.to_numeric(merged["単価"], errors="coerce")
            merged["単重"] = pd.to_numeric(merged["製品単重"], errors="coerce")
            merged["廃棄量"] = merged["廃棄不具合数"] * merged["単重"]
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
            "単重",
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
        with self.gateway.session() as session:
            qr_lots = self._qr_history_lots(session, date_from, date_to)
            if qr_lots.empty:
                return pd.DataFrame()

            defects = self._defects_for_lots(
                session,
                qr_lots["生産ロットID"].dropna().astype(str).tolist(),
                DISPOSAL_DEFECT_COLUMNS,
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

            master = self._product_master_for_parts(session, defects["品番"].dropna().astype(str).tolist())
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

        quantity = pd.to_numeric(details["数量"], errors="coerce").fillna(0).sum()
        defect_count = pd.to_numeric(details["総不具合数"], errors="coerce").fillna(0).sum()
        summary = {
            "quantity": int(quantity),
            "defect_count": int(defect_count),
            "defect_rate": (float(defect_count) / float(quantity)) if quantity else None,
        }
        for label, _ in DEFECT_FIELDS:
            if label in details.columns:
                value = pd.to_numeric(details[label], errors="coerce").fillna(0).sum()
                summary[label] = int(value) if value else None
            else:
                summary[label] = None
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

    def _defects_between(
        self,
        session: AccessSession,
        date_from: date,
        date_to: date | None,
    ) -> pd.DataFrame:
        if date_to is None:
            sql = f"""
                SELECT {self._select_clause(SOURCE_DEFECT_COLUMNS)}
                FROM t_不具合情報
                WHERE 生産ロットID LIKE 'P%%'
                  AND 総不具合数 > 0
            """
            dataframe = session.fetch_dataframe(sql)
        else:
            sql = f"""
                SELECT {self._select_clause(SOURCE_DEFECT_COLUMNS)}
                FROM t_不具合情報
                WHERE 指示日 BETWEEN ? AND ?
                  AND 生産ロットID LIKE 'P%%'
                  AND 総不具合数 > 0
            """
            dataframe = session.fetch_dataframe(sql, [date_from, date_to])
        return self._ensure_columns(dataframe, SOURCE_DEFECT_COLUMNS)

    def _defects_for_part(
        self,
        session: AccessSession,
        part_number: str,
        date_from: date,
        date_to: date,
    ) -> pd.DataFrame:
        sql = f"""
            SELECT {self._select_clause(SOURCE_DEFECT_COLUMNS)}
            FROM t_不具合情報
            WHERE 品番 = ?
              AND 指示日 BETWEEN ? AND ?
            ORDER BY 指示日 DESC, ID DESC
        """
        dataframe = session.fetch_dataframe(sql, [part_number, date_from, date_to])
        return self._ensure_columns(dataframe, SOURCE_DEFECT_COLUMNS)

    def _defects_for_lots(
        self,
        session: AccessSession,
        lot_ids: list[str],
        columns: list[str],
    ) -> pd.DataFrame:
        unique_lots = sorted({lot_id for lot_id in lot_ids if lot_id})
        if not unique_lots:
            return pd.DataFrame(columns=columns)

        frames: list[pd.DataFrame] = []
        for chunk in self._chunked(unique_lots, size=200):
            placeholders = ", ".join("?" for _ in chunk)
            sql = f"""
                SELECT {self._select_clause(columns)}
                FROM t_不具合情報
                WHERE 生産ロットID IN ({placeholders})
            """
            frames.append(session.fetch_dataframe(sql, chunk))

        if not frames:
            return pd.DataFrame(columns=columns)
        dataframe = pd.concat(frames, ignore_index=True)
        return self._ensure_columns(dataframe, columns)

    def _product_master_for_parts(self, session: AccessSession, part_numbers: list[str]) -> pd.DataFrame:
        unique_parts = sorted({part for part in part_numbers if part})
        if not unique_parts:
            return pd.DataFrame(columns=PRODUCT_MASTER_COLUMNS)

        missing_parts = [part for part in unique_parts if part not in self._product_master_cache]
        if missing_parts:
            frames: list[pd.DataFrame] = []
            for chunk in self._chunked(missing_parts, size=200):
                placeholders = ", ".join("?" for _ in chunk)
                sql = f"""
                    SELECT 製品番号, 製品単重, 材質, 単価, 材料識別, 客先名
                    FROM t_製品マスタ
                    WHERE 製品番号 IN ({placeholders})
                """
                frames.append(session.fetch_dataframe(sql, chunk))

            if frames:
                loaded = pd.concat(frames, ignore_index=True)
                loaded = self._ensure_columns(loaded, PRODUCT_MASTER_COLUMNS)
                for row in loaded.to_dict("records"):
                    product_number = str(row["製品番号"])
                    self._product_master_cache[product_number] = row

        cached_rows = [
            self._product_master_cache[part]
            for part in unique_parts
            if part in self._product_master_cache
        ]
        return pd.DataFrame(cached_rows, columns=PRODUCT_MASTER_COLUMNS)

    def _qr_history_lots(self, session: AccessSession, date_from: date, date_to: date) -> pd.DataFrame:
        sql = """
            SELECT DISTINCT 生産ロットID
            FROM t_QR履歴
            WHERE 日付 BETWEEN ? AND ?
              AND 工程コード = '03'
        """
        dataframe = session.fetch_dataframe(sql, [date_from, date_to])
        return self._ensure_columns(dataframe, ["生産ロットID"])

    def _select_clause(self, columns: list[str]) -> str:
        return ", ".join(f"[{column}]" for column in columns)

    def _ensure_columns(self, dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        normalized = dataframe.copy()
        for column in columns:
            if column not in normalized.columns:
                normalized[column] = None
        return normalized.loc[:, columns]

    def _chunked(self, values: list[str], size: int) -> list[list[str]]:
        return [values[index:index + size] for index in range(0, len(values), size)]

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from defect_information_search.infrastructure.access_gateway import AccessGateway, AccessSession
from defect_information_search.models import DEFECT_FIELDS


SUMMARY_ALIASES = {label: f"合計{index}" for index, (label, _) in enumerate(DEFECT_FIELDS, start=1)}


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


@dataclass
class SearchResult:
    summary: dict[str, Any]
    details: pd.DataFrame
    machines: list[str]


class DefectService:
    def __init__(self, gateway: AccessGateway) -> None:
        self.gateway = gateway
        self._numeric_inspectors_cache: pd.DataFrame | None = None
        self._product_master_cache: dict[str, dict[str, Any]] = {}

    def find_products(self, keyword: str) -> pd.DataFrame:
        rows = self.gateway.fetch_all(
            """
            SELECT DISTINCT 品番, 品名, 客先
            FROM t_現品票検索用
            WHERE 品番 LIKE ?
            ORDER BY 品番
            """,
            [f"*{keyword}*"],
        )
        return pd.DataFrame(rows, columns=["品番", "品名", "客先"])

    def load_search_result(
        self,
        part_number: str,
        date_from: date,
        date_to: date,
        machine: str | None,
    ) -> SearchResult:
        with self.gateway.session() as session:
            summary = self._get_summary(session, part_number, date_from, date_to, machine)
            details = self._get_details(session, part_number, date_from, date_to, machine)
            machines = self._get_machines(session, part_number, date_from, date_to)
        return SearchResult(
            summary=summary,
            details=details,
            machines=["全て", *machines] if machines else ["全て"],
        )

    def export_all_defects(self, date_from: date, date_to: date) -> pd.DataFrame:
        rows = self.gateway.fetch_all(
            """
            SELECT *
            FROM t_不具合情報
            WHERE 指示日 BETWEEN ? AND ?
            ORDER BY 品番, 指示日
            """,
            [date_from, date_to],
        )
        return pd.DataFrame(rows)

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
        return merged.loc[:, columns].sort_values(["品番", "指示日"]).reset_index(drop=True)

    def export_disposal(self, date_from: date, date_to: date) -> pd.DataFrame:
        with self.gateway.session() as session:
            defects = self._defects_between(session, date_from, date_to=None)
            if defects.empty:
                return defects

            defects["廃棄数"] = defects["総不具合数"].fillna(0) - defects["切粉"].fillna(0)
            defects = defects[
                (defects["廃棄数"] > 0)
                & defects["生産ロットID"].fillna("").astype(str).str.startswith("P")
            ].copy()
            if defects.empty:
                return defects

            qr_lots = self._qr_history_lots(session, date_from, date_to)
            if qr_lots.empty:
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
        return merged.loc[:, columns].drop_duplicates().sort_values(["品番", "生産ロットID"]).reset_index(drop=True)

    def _get_summary(
        self,
        session: AccessSession,
        part_number: str,
        date_from: date,
        date_to: date,
        machine: str | None,
    ) -> dict[str, Any]:
        conditions = ["指示日 BETWEEN ? AND ?", "品番 = ?"]
        params: list[Any] = [date_from, date_to, part_number]
        if machine:
            conditions.append("号機 = ?")
            params.append(machine)

        select_parts = [
            "品番",
            "Sum(数量) AS 数量合計",
            "Sum(総不具合数) AS 総不具合数合計",
        ]
        select_parts.extend(
            f"Sum([{label}]) AS [{SUMMARY_ALIASES[label]}]" for label, _ in DEFECT_FIELDS
        )
        row = session.fetch_one(
            f"""
            SELECT {", ".join(select_parts)}
            FROM t_不具合情報
            WHERE {" AND ".join(conditions)}
            GROUP BY 品番
            """,
            params,
        )
        if not row:
            return {}

        quantity = row.get("数量合計") or 0
        defect_count = row.get("総不具合数合計") or 0
        summary = {
            "quantity": quantity,
            "defect_count": defect_count,
            "defect_rate": (defect_count / quantity) if quantity else None,
        }
        for label, _ in DEFECT_FIELDS:
            summary[label] = row.get(SUMMARY_ALIASES[label]) or None
        return summary

    def _get_details(
        self,
        session: AccessSession,
        part_number: str,
        date_from: date,
        date_to: date,
        machine: str | None,
    ) -> pd.DataFrame:
        defects = self._defects_for_part(session, part_number, date_from, date_to, machine)
        if defects.empty:
            return pd.DataFrame(columns=DETAIL_COLUMNS)

        lot_ids = defects["生産ロットID"].dropna().astype(str).unique().tolist()
        numeric_records = self._numeric_inspection_records(session, lot_ids)
        inspectors = self._numeric_inspectors(session)

        if not numeric_records.empty:
            defects = defects.merge(numeric_records, on="生産ロットID", how="left")
        if not inspectors.empty and "検査員ID" in defects.columns:
            defects = defects.merge(inspectors, on="検査員ID", how="left")
        else:
            defects["数値検査員"] = None

        for column in DETAIL_COLUMNS:
            if column not in defects.columns:
                defects[column] = None
        return defects.loc[:, DETAIL_COLUMNS].reset_index(drop=True)

    def _get_machines(
        self,
        session: AccessSession,
        part_number: str,
        date_from: date,
        date_to: date,
    ) -> list[str]:
        rows = session.fetch_all(
            """
            SELECT DISTINCT 号機
            FROM t_不具合情報
            WHERE 品番 = ?
              AND 指示日 BETWEEN ? AND ?
            ORDER BY 号機
            """,
            [part_number, date_from, date_to],
        )
        return [str(row["号機"]) for row in rows if row.get("号機")]

    def _defects_between(
        self,
        session: AccessSession,
        date_from: date,
        date_to: date | None,
    ) -> pd.DataFrame:
        if date_to is None:
            rows = session.fetch_all("SELECT * FROM t_不具合情報")
        else:
            rows = session.fetch_all(
                """
                SELECT *
                FROM t_不具合情報
                WHERE 指示日 BETWEEN ? AND ?
                """,
                [date_from, date_to],
            )
        return pd.DataFrame(rows)

    def _defects_for_part(
        self,
        session: AccessSession,
        part_number: str,
        date_from: date,
        date_to: date,
        machine: str | None,
    ) -> pd.DataFrame:
        sql = """
            SELECT *
            FROM t_不具合情報
            WHERE 品番 = ?
              AND 指示日 BETWEEN ? AND ?
        """
        params: list[Any] = [part_number, date_from, date_to]
        if machine:
            sql += " AND 号機 = ?"
            params.append(machine)
        sql += " ORDER BY 指示日 DESC"
        rows = session.fetch_all(sql, params)
        return pd.DataFrame(rows)

    def _numeric_inspection_records(self, session: AccessSession, lot_ids: list[str]) -> pd.DataFrame:
        if not lot_ids:
            return pd.DataFrame(columns=["生産ロットID", "検査員ID"])
        placeholders = ", ".join("?" for _ in lot_ids)
        rows = session.fetch_all(
            f"""
            SELECT 生産ロットID, 検査員ID
            FROM t_数値検査記録
            WHERE 生産ロットID IN ({placeholders})
            """,
            lot_ids,
        )
        return pd.DataFrame(rows)

    def _numeric_inspectors(self, session: AccessSession) -> pd.DataFrame:
        if self._numeric_inspectors_cache is None:
            rows = session.fetch_all(
                """
                SELECT 検査員ID, 検査員名 AS 数値検査員
                FROM t_数値検査員マスタ
                """
            )
            self._numeric_inspectors_cache = pd.DataFrame(rows)
        return self._numeric_inspectors_cache.copy()

    def _product_master_for_parts(self, session: AccessSession, part_numbers: list[str]) -> pd.DataFrame:
        unique_parts = sorted({part for part in part_numbers if part})
        if not unique_parts:
            return pd.DataFrame(columns=["製品番号", "製品単重", "材質", "単価", "材料識別", "客先名"])

        missing_parts = [part for part in unique_parts if part not in self._product_master_cache]
        if missing_parts:
            placeholders = ", ".join("?" for _ in missing_parts)
            rows = session.fetch_all(
                f"""
                SELECT 製品番号, 製品単重, 材質, 単価, 材料識別, 客先名
                FROM t_製品マスタ
                WHERE 製品番号 IN ({placeholders})
                """,
                missing_parts,
            )
            for row in rows:
                product_number = str(row["製品番号"])
                self._product_master_cache[product_number] = row

        cached_rows = [
            self._product_master_cache[part]
            for part in unique_parts
            if part in self._product_master_cache
        ]
        return pd.DataFrame(cached_rows)

    def _qr_history_lots(self, session: AccessSession, date_from: date, date_to: date) -> pd.DataFrame:
        rows = session.fetch_all(
            """
            SELECT DISTINCT 生産ロットID
            FROM t_QR履歴
            WHERE 日付 BETWEEN ? AND ?
              AND 工程コード = '03'
            """,
            [date_from, date_to],
        )
        return pd.DataFrame(rows)

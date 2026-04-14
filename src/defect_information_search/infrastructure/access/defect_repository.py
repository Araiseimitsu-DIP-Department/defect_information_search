from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path

import pandas as pd
import pyodbc

from defect_information_search.application.ports.defect_repository import DefectRepository
from defect_information_search.domain.models import DefectRecord, ProductCatalogItem, ProductMasterItem, QrHistoryItem
from defect_information_search.infrastructure.access_gateway import AccessGateway
from defect_information_search.infrastructure.mappers.domain_mappers import (
    defect_records_from_frame,
    product_catalog_items_from_frame,
    product_master_items_from_frame,
    qr_history_items_from_frame,
)
from defect_information_search.shared.errors import RepositoryError


PRODUCT_CATALOG_COLUMNS = ["品番", "品名", "客先"]
SOURCE_DEFECT_COLUMNS = [
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
]
PRODUCT_MASTER_COLUMNS = ["製品番号", "製品単重", "材質", "単価", "材料識別", "客先名"]


class AccessDefectRepository(DefectRepository):
    def __init__(self, access_db_path: Path) -> None:
        self._gateway = AccessGateway(access_db_path)

    def find_products(self, keyword: str) -> Sequence[ProductCatalogItem]:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return []

        pattern = f"%{normalized_keyword}%"
        sql = """
            SELECT DISTINCT [品番], [品名], [客先]
            FROM [t_現品票検索用]
            WHERE [品番] LIKE ?
               OR [品名] LIKE ?
               OR [客先] LIKE ?
            ORDER BY [品番]
        """
        frame = self._fetch_dataframe(sql, [pattern, pattern, pattern]).reset_index(drop=True)
        return product_catalog_items_from_frame(frame)

    def find_defects_for_part(self, part_number: str, date_from: date, date_to: date) -> Sequence[DefectRecord]:
        sql = """
            SELECT *
            FROM [t_不具合情報]
            WHERE [品番] = ?
              AND [指示日] BETWEEN ? AND ?
            ORDER BY [指示日] DESC, [ID] DESC
        """
        frame = self._fetch_dataframe(sql, [part_number, date_from, date_to]).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_defects_between(self, date_from: date, date_to: date | None = None) -> Sequence[DefectRecord]:
        if date_to is None:
            sql = """
                SELECT *
                FROM [t_不具合情報]
                WHERE [生産ロットID] LIKE 'P%%'
                  AND [総不具合数] > 0
            """
            frame = self._fetch_dataframe(sql).reset_index(drop=True)
            return defect_records_from_frame(frame)

        sql = """
            SELECT *
            FROM [t_不具合情報]
            WHERE [指示日] BETWEEN ? AND ?
              AND [生産ロットID] LIKE 'P%%'
              AND [総不具合数] > 0
        """
        frame = self._fetch_dataframe(sql, [date_from, date_to]).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_qr_history_lots(self, date_from: date, date_to: date) -> Sequence[QrHistoryItem]:
        sql = """
            SELECT DISTINCT [生産ロットID]
            FROM [t_QR履歴]
            WHERE [日付] BETWEEN ? AND ?
              AND [工程コード] = '03'
        """
        frame = self._fetch_dataframe(sql, [date_from, date_to]).reset_index(drop=True)
        return qr_history_items_from_frame(frame)

    def find_defects_for_lots(self, lot_ids: Sequence[str]) -> Sequence[DefectRecord]:
        unique_lots = sorted({lot_id for lot_id in lot_ids if lot_id})
        if not unique_lots:
            return []

        frames: list[pd.DataFrame] = []
        with self._gateway.session() as session:
            for chunk in self._chunked(unique_lots, size=200):
                placeholders = ", ".join("?" for _ in chunk)
                sql = f"""
                    SELECT *
                    FROM [t_不具合情報]
                    WHERE [生産ロットID] IN ({placeholders})
                """
                frames.append(self._safe_fetch_dataframe(session.fetch_dataframe, sql, chunk))

        if not frames:
            return []
        frame = pd.concat(frames, ignore_index=True).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_product_master_for_parts(self, part_numbers: Sequence[str]) -> Sequence[ProductMasterItem]:
        unique_parts = sorted({part for part in part_numbers if part})
        if not unique_parts:
            return []

        frames: list[pd.DataFrame] = []
        with self._gateway.session() as session:
            for chunk in self._chunked(unique_parts, size=200):
                placeholders = ", ".join("?" for _ in chunk)
                sql = f"""
                    SELECT [製品番号], [製品名], [客先名], [材質], [単価], [製品単重], [材料識別], [次工程]
                    FROM [t_製品マスタ]
                    WHERE [製品番号] IN ({placeholders})
                """
                frames.append(self._safe_fetch_dataframe(session.fetch_dataframe, sql, chunk))

        if not frames:
            return []
        frame = pd.concat(frames, ignore_index=True).reset_index(drop=True)
        return product_master_items_from_frame(frame)

    def iter_all_defects(self, date_from: date, date_to: date) -> tuple[Sequence[str], Iterable[Sequence[object]]]:
        sql = """
            SELECT
                [ID],
                [生産ロットID],
                [品番],
                [指示日],
                [号機],
                [検査者1],
                [検査者2],
                [検査者3],
                [検査者4],
                [検査者5],
                [時間],
                [数量],
                [総不具合数],
                [不良率],
                [外観キズ],
                [圧痕],
                [切粉],
                [毟れ],
                [穴大],
                [穴小],
                [穴キズ],
                [バリ],
                [短寸],
                [面粗],
                [サビ],
                [ボケ],
                [挽目],
                [汚れ],
                [メッキ],
                [落下],
                [フクレ],
                [ツブレ],
                [ボッチ],
                [段差],
                [バレル石],
                [径プラス],
                [径マイナス],
                [ゲージ],
                [異物混入],
                [形状不良],
                [こすれ],
                [変色シミ],
                [材料キズ],
                [ゴミ],
                [その他],
                [その他内容]
            FROM [t_不具合情報]
            WHERE [指示日] BETWEEN ? AND ?
            ORDER BY [品番], [指示日], [ID]
        """
        dataframe = self._fetch_dataframe(sql, [date_from, date_to])
        return list(dataframe.columns), dataframe.itertuples(index=False, name=None)

    @staticmethod
    def _chunked(values: list[str], size: int) -> list[list[str]]:
        return [values[index:index + size] for index in range(0, len(values), size)]

    def _fetch_dataframe(self, sql: str, params: list[object] | None = None) -> pd.DataFrame:
        try:
            return self._gateway.fetch_dataframe(sql, params)
        except (pyodbc.Error, RepositoryError) as exc:
            raise RepositoryError(str(exc)) from exc

    def _safe_fetch_dataframe(self, fetcher, sql: str, params: Sequence[object]) -> pd.DataFrame:
        try:
            return fetcher(sql, params)
        except (pyodbc.Error, RepositoryError) as exc:
            raise RepositoryError(str(exc)) from exc

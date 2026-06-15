from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

import pandas as pd
import psycopg
from psycopg import sql as pg_sql

from defect_information_search.application.ports.defect_repository import DefectRepository
from defect_information_search.domain.models import DefectRecord, ProductCatalogItem, ProductMasterItem, QrHistoryItem
from defect_information_search.infrastructure.mappers.domain_mappers import (
    defect_records_frame_from_items,
    defect_records_from_frame,
    product_catalog_items_from_frame,
    product_master_items_from_frame,
    qr_history_items_from_frame,
)
from defect_information_search.shared.errors import RepositoryError


DEFECT_COLUMNS = """
    id,
    production_lot_id,
    product_code AS part_number,
    instruction_date::date AS instruction_date,
    machine_no,
    inspector_1,
    inspector_2,
    inspector_3,
    inspector_4,
    inspector_5,
    time_value AS work_minutes,
    quantity,
    total_defect_count,
    defect_rate,
    appearance_scratch,
    dent,
    cutting_chip AS chip,
    mushire AS tear,
    oversized_hole AS hole_large,
    undersized_hole AS hole_small,
    hole_scratch,
    burr,
    short_length,
    rough_surface,
    rust,
    blur,
    turning_mark,
    stain,
    plating,
    dropped AS drop_damage,
    swelling AS blister,
    crush,
    bump AS projection,
    step,
    barrel_stone,
    diameter_plus,
    diameter_minus,
    gauge,
    foreign_matter,
    shape_defect,
    abrasion AS rub_mark,
    discoloration_stain AS discoloration,
    material_scratch,
    dust,
    other,
    other_detail
"""


class PostgresDefectRepository(DefectRepository):
    def __init__(
        self,
        dsn: str | None = None,
        schema: str = "public",
        *,
        appearance_dsn: str | None = None,
        delivery_label_dsn: str | None = None,
        delivery_label_search_dsn: str | None = None,
        arai_masters_dsn: str | None = None,
    ) -> None:
        self._appearance_dsn = appearance_dsn or dsn
        self._delivery_label_dsn = delivery_label_dsn or dsn
        self._delivery_label_search_dsn = delivery_label_search_dsn or self._delivery_label_dsn or dsn
        self._arai_masters_dsn = arai_masters_dsn or dsn
        if not all(
            (
                self._appearance_dsn,
                self._delivery_label_dsn,
                self._delivery_label_search_dsn,
                self._arai_masters_dsn,
            )
        ):
            raise RepositoryError("PostgreSQL connection URLs are not configured.")
        self._schema = schema or "public"

    def find_products(self, keyword: str) -> Sequence[ProductCatalogItem]:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return []

        pattern = f"%{normalized_keyword}%"
        query = """
            SELECT DISTINCT
                product_code AS part_number,
                product_name AS part_name,
                customer AS customer_name
            FROM delivery_label_search
            WHERE product_code LIKE %s
               OR product_name LIKE %s
               OR customer LIKE %s
            ORDER BY product_code
        """
        frame = self._fetch_dataframe(
            self._delivery_label_search_dsn, query, [pattern, pattern, pattern]
        ).reset_index(drop=True)
        return product_catalog_items_from_frame(frame)

    def find_defects_for_part(self, part_number: str, date_from: date, date_to: date) -> Sequence[DefectRecord]:
        query = f"""
            SELECT {DEFECT_COLUMNS}
            FROM defect_information
            WHERE product_code = %s
              AND instruction_date::date BETWEEN %s AND %s
            ORDER BY instruction_date DESC, id DESC
        """
        frame = self._fetch_dataframe(self._appearance_dsn, query, [part_number, date_from, date_to]).reset_index(drop=True)
        frame = self._attach_numeric_inspectors(frame)
        return defect_records_from_frame(frame)

    def find_defects_between(self, date_from: date, date_to: date | None = None) -> Sequence[DefectRecord]:
        if date_to is None:
            query = f"""
                SELECT {DEFECT_COLUMNS}
                FROM defect_information
                WHERE production_lot_id LIKE 'P%%'
                  AND total_defect_count > 0
            """
            frame = self._fetch_dataframe(self._appearance_dsn, query).reset_index(drop=True)
            return defect_records_from_frame(frame)

        query = f"""
            SELECT {DEFECT_COLUMNS}
            FROM defect_information
            WHERE instruction_date::date BETWEEN %s AND %s
              AND production_lot_id LIKE 'P%%'
              AND total_defect_count > 0
        """
        frame = self._fetch_dataframe(self._appearance_dsn, query, [date_from, date_to]).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_qr_history_lots(self, date_from: date, date_to: date) -> Sequence[QrHistoryItem]:
        query = """
            SELECT DISTINCT production_lot_id
            FROM qr_history
            WHERE date_value::date BETWEEN %s AND %s
              AND process_code = '03'
        """
        frame = self._fetch_dataframe(self._delivery_label_dsn, query, [date_from, date_to]).reset_index(drop=True)
        return qr_history_items_from_frame(frame)

    def find_defects_for_lots(self, lot_ids: Sequence[str]) -> Sequence[DefectRecord]:
        unique_lots = sorted({lot_id for lot_id in lot_ids if lot_id})
        if not unique_lots:
            return []

        frames: list[pd.DataFrame] = []
        for chunk in self._chunked(unique_lots, size=500):
            placeholders = ", ".join(["%s"] * len(chunk))
            query = f"""
                SELECT {DEFECT_COLUMNS}
                FROM defect_information
                WHERE production_lot_id IN ({placeholders})
            """
            frames.append(self._fetch_dataframe(self._appearance_dsn, query, chunk))

        if not frames:
            return []
        frame = pd.concat(frames, ignore_index=True).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_product_master_for_parts(self, part_numbers: Sequence[str]) -> Sequence[ProductMasterItem]:
        unique_parts = sorted({part for part in part_numbers if part})
        if not unique_parts:
            return []

        frames: list[pd.DataFrame] = []
        for chunk in self._chunked(unique_parts, size=500):
            placeholders = ", ".join(["%s"] * len(chunk))
            query = f"""
                SELECT
                    product_number,
                    product_name,
                    customer_name,
                    material,
                    unit_price,
                    unit_weight,
                    material_type,
                    next_process
                FROM (
                    SELECT
                        product_no AS product_number,
                        product_name,
                        customer_name,
                        material_and_diameter AS material,
                        unit_price,
                        unit_weight,
                        CASE
                            WHEN NULLIF(material_identification, '') ~ '^[0-9]+$'
                                THEN material_identification::integer
                            ELSE NULL
                        END AS material_type,
                        next_process
                    FROM product_master
                ) AS master
                WHERE product_number IN ({placeholders})
            """
            frames.append(self._fetch_dataframe(self._arai_masters_dsn, query, chunk))

        if not frames:
            return []
        frame = pd.concat(frames, ignore_index=True).reset_index(drop=True)
        return product_master_items_from_frame(frame)

    def iter_all_defects(self, date_from: date, date_to: date) -> tuple[Sequence[str], Iterable[Sequence[object]]]:
        query = f"""
            SELECT {DEFECT_COLUMNS}
            FROM defect_information
            WHERE instruction_date::date BETWEEN %s AND %s
            ORDER BY product_code, instruction_date, id
        """
        dataframe = self._fetch_dataframe(self._appearance_dsn, query, [date_from, date_to])
        dataframe = pd.DataFrame(defect_records_frame_from_items(defect_records_from_frame(dataframe)))
        return list(dataframe.columns), dataframe.itertuples(index=False, name=None)

    @staticmethod
    def _chunked(values: list[str], size: int) -> list[list[str]]:
        return [values[index:index + size] for index in range(0, len(values), size)]

    def _attach_numeric_inspectors(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty or "production_lot_id" not in frame.columns:
            return frame

        lot_ids = sorted({str(lot_id) for lot_id in frame["production_lot_id"].dropna() if str(lot_id)})
        if not lot_ids:
            frame["inspector_name"] = None
            return frame

        inspector_rows: list[pd.DataFrame] = []
        for chunk in self._chunked(lot_ids, size=500):
            placeholders = ", ".join(["%s"] * len(chunk))
            query = f"""
                SELECT DISTINCT ON (production_lot_id)
                    production_lot_id,
                    inspector_id
                FROM numeric_inspection_records
                WHERE production_lot_id IN ({placeholders})
                ORDER BY production_lot_id, inspected_at DESC NULLS LAST, id DESC
            """
            inspector_rows.append(self._fetch_dataframe(self._appearance_dsn, query, chunk))

        inspector_frame = pd.concat(inspector_rows, ignore_index=True) if inspector_rows else pd.DataFrame()
        inspector_ids = sorted({str(value) for value in inspector_frame.get("inspector_id", pd.Series(dtype=object)).dropna()})
        if not inspector_ids:
            frame["inspector_name"] = None
            return frame

        name_rows: list[pd.DataFrame] = []
        for chunk in self._chunked(inspector_ids, size=500):
            placeholders = ", ".join(["%s"] * len(chunk))
            query = f"""
                SELECT inspector_id, inspector_name
                FROM numeric_inspector_master
                WHERE inspector_id IN ({placeholders})
            """
            name_rows.append(self._fetch_dataframe(self._appearance_dsn, query, chunk))

        name_frame = pd.concat(name_rows, ignore_index=True) if name_rows else pd.DataFrame()
        enriched = inspector_frame.merge(name_frame, on="inspector_id", how="left")
        return frame.drop(columns=["inspector_name"], errors="ignore").merge(enriched, on="production_lot_id", how="left")

    def _fetch_dataframe(
        self,
        dsn: str | None,
        query: str,
        params: Sequence[object] | None = None,
    ) -> pd.DataFrame:
        if not dsn:
            raise RepositoryError("PostgreSQL connection URL is not configured.")
        try:
            with psycopg.connect(dsn, connect_timeout=30) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        pg_sql.SQL("SET search_path TO {}").format(pg_sql.Identifier(self._schema))
                    )
                    cursor.execute(query, tuple(params or ()))
                    rows = cursor.fetchall()
                    columns = [column.name for column in cursor.description] if cursor.description else []
        except psycopg.Error as exc:
            raise RepositoryError(str(exc)) from exc

        if not rows:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame.from_records(rows, columns=columns)

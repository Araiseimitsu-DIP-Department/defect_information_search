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
    part_number,
    instruction_date,
    machine_no,
    inspector_1,
    inspector_2,
    inspector_3,
    inspector_4,
    inspector_5,
    work_minutes,
    quantity,
    total_defect_count,
    defect_rate,
    appearance_scratch,
    dent,
    chip,
    tear,
    hole_large,
    hole_small,
    hole_scratch,
    burr,
    short_length,
    rough_surface,
    rust,
    blur,
    turning_mark,
    stain,
    plating,
    drop_damage,
    blister,
    crush,
    projection,
    step,
    barrel_stone,
    diameter_plus,
    diameter_minus,
    gauge,
    foreign_matter,
    shape_defect,
    rub_mark,
    discoloration,
    material_scratch,
    dust,
    other,
    other_detail
"""


class PostgresDefectRepository(DefectRepository):
    def __init__(self, dsn: str | None = None, schema: str = "public") -> None:
        if not dsn:
            raise RepositoryError("POSTGRES_CONNECTION_URL is not configured.")
        self._dsn = dsn
        self._schema = schema or "public"

    def find_products(self, keyword: str) -> Sequence[ProductCatalogItem]:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return []

        pattern = f"%{normalized_keyword}%"
        query = """
            SELECT DISTINCT
                part_number,
                part_name,
                customer_name
            FROM product_catalog
            WHERE part_number LIKE %s
               OR part_name LIKE %s
               OR customer_name LIKE %s
            ORDER BY part_number
        """
        frame = self._fetch_dataframe(query, [pattern, pattern, pattern]).reset_index(drop=True)
        return product_catalog_items_from_frame(frame)

    def find_defects_for_part(self, part_number: str, date_from: date, date_to: date) -> Sequence[DefectRecord]:
        query = f"""
            SELECT
                d.*,
                im.inspector_name
            FROM (
                SELECT {DEFECT_COLUMNS}
                FROM defect_records
                WHERE part_number = %s
                  AND instruction_date BETWEEN %s AND %s
            ) AS d
            LEFT JOIN inspection_records ir
              ON d.production_lot_id = ir.production_lot_id
            LEFT JOIN inspector_master im
              ON ir.inspector_id = im.inspector_id
            ORDER BY d.instruction_date DESC, d.id DESC
        """
        frame = self._fetch_dataframe(query, [part_number, date_from, date_to]).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_defects_between(self, date_from: date, date_to: date | None = None) -> Sequence[DefectRecord]:
        if date_to is None:
            query = f"""
                SELECT {DEFECT_COLUMNS}
                FROM defect_records
                WHERE production_lot_id LIKE 'P%%'
                  AND total_defect_count > 0
            """
            frame = self._fetch_dataframe(query).reset_index(drop=True)
            return defect_records_from_frame(frame)

        query = f"""
            SELECT {DEFECT_COLUMNS}
            FROM defect_records
            WHERE instruction_date BETWEEN %s AND %s
              AND production_lot_id LIKE 'P%%'
              AND total_defect_count > 0
        """
        frame = self._fetch_dataframe(query, [date_from, date_to]).reset_index(drop=True)
        return defect_records_from_frame(frame)

    def find_qr_history_lots(self, date_from: date, date_to: date) -> Sequence[QrHistoryItem]:
        query = """
            SELECT DISTINCT production_lot_id
            FROM qr_history
            WHERE event_at::date BETWEEN %s AND %s
              AND process_code = '03'
        """
        frame = self._fetch_dataframe(query, [date_from, date_to]).reset_index(drop=True)
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
                FROM defect_records
                WHERE production_lot_id IN ({placeholders})
            """
            frames.append(self._fetch_dataframe(query, chunk))

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
                FROM product_master
                WHERE product_number IN ({placeholders})
            """
            frames.append(self._fetch_dataframe(query, chunk))

        if not frames:
            return []
        frame = pd.concat(frames, ignore_index=True).reset_index(drop=True)
        return product_master_items_from_frame(frame)

    def iter_all_defects(self, date_from: date, date_to: date) -> tuple[Sequence[str], Iterable[Sequence[object]]]:
        query = f"""
            SELECT {DEFECT_COLUMNS}
            FROM defect_records
            WHERE instruction_date BETWEEN %s AND %s
            ORDER BY part_number, instruction_date, id
        """
        dataframe = self._fetch_dataframe(query, [date_from, date_to])
        dataframe = pd.DataFrame(defect_records_frame_from_items(defect_records_from_frame(dataframe)))
        return list(dataframe.columns), dataframe.itertuples(index=False, name=None)

    @staticmethod
    def _chunked(values: list[str], size: int) -> list[list[str]]:
        return [values[index:index + size] for index in range(0, len(values), size)]

    def _fetch_dataframe(self, query: str, params: Sequence[object] | None = None) -> pd.DataFrame:
        try:
            with psycopg.connect(self._dsn, connect_timeout=30) as connection:
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

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from defect_information_search.infrastructure.postgres.defect_repository import PostgresDefectRepository


def main() -> int:
    load_dotenv(ROOT_DIR / ".env", override=True)
    appearance_dsn = os.environ["POSTGRES_APPEARANCE_CONNECTION_URL"]
    delivery_label_dsn = os.environ["POSTGRES_DELIVERY_LABEL_CONNECTION_URL"]
    delivery_label_search_dsn = os.environ["POSTGRES_DELIVERY_LABEL_SEARCH_CONNECTION_URL"]
    arai_masters_dsn = os.environ["POSTGRES_ARAI_MASTERS_CONNECTION_URL"]
    schema = os.getenv("POSTGRES_SCHEMA", "public")

    import psycopg

    with psycopg.connect(appearance_dsn, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT product_code, min(instruction_date)::date, max(instruction_date)::date
                FROM public.defect_information
                WHERE nullif(btrim(product_code), '') IS NOT NULL
                GROUP BY product_code
                ORDER BY count(*) DESC
                LIMIT 1
                """
            )
            part_number, date_from, date_to = cursor.fetchone()

    with psycopg.connect(delivery_label_dsn, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT min(date_value)::date, max(date_value)::date
                FROM public.qr_history
                WHERE process_code = '03'
                """
            )
            qr_from, qr_to = cursor.fetchone()

    repository = PostgresDefectRepository(
        os.getenv("POSTGRES_CONNECTION_URL"),
        schema,
        appearance_dsn=appearance_dsn,
        delivery_label_dsn=delivery_label_dsn,
        delivery_label_search_dsn=delivery_label_search_dsn,
        arai_masters_dsn=arai_masters_dsn,
    )
    products = repository.find_products(part_number[:3])
    defects = repository.find_defects_for_part(part_number, date_from, date_to)
    non_null_work_minutes = sum(1 for record in defects if record.work_minutes is not None)
    defects_between = repository.find_defects_between(date_from, date_to)
    qr_lots = repository.find_qr_history_lots(qr_from, qr_to)
    lot_defects = repository.find_defects_for_lots([item.lot_id for item in qr_lots[:5]])
    masters = repository.find_product_master_for_parts([part_number])
    columns, rows = repository.iter_all_defects(date_from, date_to)
    sample_rows = sum(1 for _, _row in zip(range(3), rows))

    print(f"part={part_number} range={date_from}..{date_to} qr_range={qr_from}..{qr_to}")
    print(f"products={len(products)}")
    print(f"defects_for_part={len(defects)}")
    print(f"defects_for_part_non_null_work_minutes={non_null_work_minutes}")
    print(f"defects_between={len(defects_between)}")
    print(f"qr_lots={len(qr_lots)}")
    print(f"lot_defects={len(lot_defects)}")
    print(f"product_masters={len(masters)}")
    print(f"iter_columns={len(columns)} iter_sample_rows={sample_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

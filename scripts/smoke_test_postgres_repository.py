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
    dsn = os.environ["POSTGRES_CONNECTION_URL"]
    schema = os.getenv("POSTGRES_SCHEMA", "public")

    import psycopg

    with psycopg.connect(dsn, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT part_number, min(instruction_date), max(instruction_date)
                FROM public.defect_records
                WHERE nullif(btrim(part_number), '') IS NOT NULL
                GROUP BY part_number
                ORDER BY count(*) DESC
                LIMIT 1
                """
            )
            part_number, date_from, date_to = cursor.fetchone()
            cursor.execute(
                """
                SELECT min(event_at)::date, max(event_at)::date
                FROM public.qr_history
                WHERE process_code = '03'
                """
            )
            qr_from, qr_to = cursor.fetchone()

    repository = PostgresDefectRepository(dsn, schema)
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

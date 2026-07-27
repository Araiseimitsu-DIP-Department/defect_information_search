from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.infrastructure.postgres.defect_repository import (
    NUMERIC_INSPECTION_PROCESS_NAME,
    PostgresDefectRepository,
)


class PostgresRepositorySqlTests(unittest.TestCase):
    def test_find_products_uses_delivery_label_history(self) -> None:
        repo = PostgresDefectRepository.__new__(PostgresDefectRepository)
        repo._delivery_label_dsn = "postgresql://delivery"
        calls: list[tuple[str | None, str, list[object] | None]] = []

        def fake_fetch_dataframe(dsn, query, params=None):
            calls.append((dsn, query, list(params) if params is not None else None))
            return pd.DataFrame(columns=["part_number", "part_name", "customer_name"])

        repo._fetch_dataframe = fake_fetch_dataframe

        repo.find_products("A001")

        dsn, query, params = calls[-1]
        self.assertEqual(dsn, "postgresql://delivery")
        self.assertIn("FROM delivery_label_history", query)
        self.assertNotIn("delivery_label_search", query)
        self.assertEqual(params, ["%A001%", "%A001%", "%A001%"])

    def test_find_products_uses_case_insensitive_matching(self) -> None:
        repo = PostgresDefectRepository.__new__(PostgresDefectRepository)
        repo._delivery_label_dsn = "postgresql://delivery"
        calls: list[tuple[str | None, str, list[object] | None]] = []

        def fake_fetch_dataframe(dsn, query, params=None):
            calls.append((dsn, query, list(params) if params is not None else None))
            return pd.DataFrame(columns=["part_number", "part_name", "customer_name"])

        repo._fetch_dataframe = fake_fetch_dataframe

        repo.find_products("3d025")

        _dsn, query, params = calls[-1]
        self.assertIn("product_code ILIKE %s", query)
        self.assertIn("product_name ILIKE %s", query)
        self.assertIn("customer ILIKE %s", query)
        self.assertEqual(params, ["%3d025%", "%3d025%", "%3d025%"])

    def test_attach_numeric_inspectors_uses_latest_positioned_qr_history(self) -> None:
        repo = PostgresDefectRepository.__new__(PostgresDefectRepository)
        repo._delivery_label_dsn = "postgresql://delivery"
        repo._appearance_dsn = "postgresql://appearance"
        calls: list[tuple[str | None, str, list[object] | None]] = []

        def fake_fetch_dataframe(dsn, query, params=None):
            calls.append((dsn, query, list(params) if params is not None else None))
            if "FROM qr_history" in query:
                return pd.DataFrame(
                    [{"_numeric_inspector_lot_id": "P157275", "inspector_id": "16"}]
                )
            if "FROM numeric_inspector_master" in query:
                return pd.DataFrame([{"inspector_id": "16", "inspector_name": "櫻井翼"}])
            raise AssertionError(f"Unexpected query: {query}")

        repo._fetch_dataframe = fake_fetch_dataframe

        result = repo._attach_numeric_inspectors(
            pd.DataFrame([{"production_lot_id": " P157275 ", "part_number": "T-110750L01"}])
        )

        qr_dsn, qr_query, qr_params = calls[0]
        self.assertEqual(qr_dsn, "postgresql://delivery")
        self.assertIn("FROM qr_history", qr_query)
        self.assertIn("TRIM(process_name) LIKE %s", qr_query)
        self.assertIn("NULLIF(TRIM(position), '') IS NOT NULL", qr_query)
        self.assertIn("date_time DESC NULLS LAST, id DESC", qr_query)
        self.assertNotIn("numeric_inspection_records", qr_query)
        self.assertEqual(qr_params, ["P157275", f"%{NUMERIC_INSPECTION_PROCESS_NAME}%"])

        master_dsn, master_query, master_params = calls[1]
        self.assertEqual(master_dsn, "postgresql://appearance")
        self.assertIn("FROM numeric_inspector_master", master_query)
        self.assertEqual(master_params, ["16"])
        self.assertEqual(result.iloc[0]["inspector_name"], "櫻井翼")


if __name__ == "__main__":
    unittest.main()

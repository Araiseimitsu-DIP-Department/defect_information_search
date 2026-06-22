from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.infrastructure.postgres.defect_repository import PostgresDefectRepository


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


if __name__ == "__main__":
    unittest.main()

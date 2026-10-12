from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.infrastructure.access.defect_repository import AccessDefectRepository


class _FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []

    def fetch_dataframe(self, sql: str, params=None) -> pd.DataFrame:
        self.calls.append((sql, tuple(params) if params is not None else None))
        return pd.DataFrame()

    def session(self):  # pragma: no cover - not used in these tests
        raise AssertionError("session should not be called")


class AccessRepositorySqlTests(unittest.TestCase):
    def test_aggregate_reads_current_and_archive_from_appearance_gateway(self):
        from datetime import date
        repo = AccessDefectRepository.__new__(AccessDefectRepository)
        repo._appearance_gateway = _FakeGateway()
        rows = repo.find_aggregate_inspections(date(2025, 10, 1), date(2026, 9, 30))
        self.assertEqual(rows, [])
        calls = repo._appearance_gateway.calls
        self.assertIn("[t_外観検査集計]", calls[0][0])
        self.assertIn("[t_外観検査集計保存]", calls[1][0])
        self.assertEqual(calls[0][1], (date(2025, 10, 1), date(2026, 10, 1)))

    def setUp(self) -> None:
        self.repo = AccessDefectRepository.__new__(AccessDefectRepository)
        self.fake_gateway = _FakeGateway()
        self.repo._gateway = self.fake_gateway

    def test_find_products_uses_current_table_name(self) -> None:
        self.repo.find_products("A001")

        sql, params = self.fake_gateway.calls[-1]
        self.assertIn("[t_現品票検索用]", sql)
        self.assertEqual(params, ("%A001%", "%A001%", "%A001%"))

    def test_find_defects_for_part_uses_current_table_name(self) -> None:
        self.repo.find_defects_for_part("A001", "2026-04-14", "2026-04-15")

        sql, params = self.fake_gateway.calls[-1]
        self.assertIn("t_不具合情報", sql)
        self.assertEqual(params, ("A001", "2026-04-14", "2026-04-15"))

    def test_find_qr_history_lots_uses_current_table_name(self) -> None:
        self.repo.find_qr_history_lots("2026-04-14", "2026-04-15")

        sql, params = self.fake_gateway.calls[-1]
        self.assertIn("[t_QR履歴]", sql)
        self.assertEqual(params, ("2026-04-14", "2026-04-15"))


if __name__ == "__main__":
    unittest.main()

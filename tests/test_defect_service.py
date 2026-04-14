from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.domain.models import DefectRecord, ProductCatalogItem
from defect_information_search.services.defect_service import DefectService


class _FakeRepository:
    def find_products(self, keyword: str):
        self.last_keyword = keyword
        return [
            ProductCatalogItem(part_number="A001", part_name="部品A", customer="顧客A"),
            ProductCatalogItem(part_number="A002", part_name=None, customer=None),
        ]

    def find_defects_for_part(self, part_number: str, date_from: date, date_to: date):
        self.last_part_number = part_number
        self.last_date_from = date_from
        self.last_date_to = date_to
        return [
            DefectRecord(
                record_id=1,
                lot_id="P001",
                part_number=part_number,
                instruction_date=date_from,
                machine_code="1",
                quantity=10,
                total_defects=2,
                defect_rate=0.2,
                defect_counts={"外観キズ": 2},
            )
        ]

    def find_defects_between(self, date_from: date, date_to: date | None = None):
        raise AssertionError("not used")

    def find_qr_history_lots(self, date_from: date, date_to: date):
        raise AssertionError("not used")

    def find_defects_for_lots(self, lot_ids):
        raise AssertionError("not used")

    def find_product_master_for_parts(self, part_numbers):
        raise AssertionError("not used")

    def iter_all_defects(self, date_from: date, date_to: date):
        raise AssertionError("not used")


class DefectServiceTests(unittest.TestCase):
    def test_find_products_accepts_domain_items(self) -> None:
        service = DefectService(_FakeRepository())

        frame = service.find_products("  A00  ")

        self.assertEqual(list(frame["品番"]), ["A001", "A002"])
        self.assertEqual(frame.iloc[0]["品名"], "部品A")
        self.assertTrue(pd.isna(frame.iloc[1]["品名"]))
        self.assertEqual(frame.iloc[0]["客先"], "顧客A")
        self.assertTrue(pd.isna(frame.iloc[1]["客先"]))

    def test_load_search_result_converts_domain_records_to_frame(self) -> None:
        service = DefectService(_FakeRepository())

        result = service.load_search_result("A001", date(2026, 4, 14), date(2026, 4, 15), None)

        self.assertFalse(result.all_details.empty)
        self.assertEqual(result.summary["quantity"], 10)
        self.assertEqual(result.summary["defect_count"], 2)
        self.assertEqual(result.summary["外観キズ"], 2)
        self.assertIn("号機", result.details.columns)
        self.assertEqual(result.details.iloc[0]["品番"], "A001")
        self.assertEqual(result.details.iloc[0]["外観キズ"], 2)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from defect_information_search.domain.models import DefectRecord, ProductMasterItem, QrHistoryItem, InspectionSummary
from defect_information_search.services.defect_service import DefectService


def record(lot: str, part: str, total: int, chip: int) -> DefectRecord:
    return DefectRecord(
        record_id=1,
        lot_id=lot,
        part_number=part,
        instruction_date=date(2026, 1, 1),
        quantity=100,
        total_defects=total,
        defect_counts={"切粉": chip},
    )


class ReportRepository:
    def __init__(self, records, masters, qr_lots=(), inspections=None):
        self.records = records
        self.masters = masters
        self.qr_lots = qr_lots
        self.inspections = inspections if inspections is not None else [
            InspectionSummary(item.record_id, item.lot_id, item.instruction_date) for item in records]

    def find_aggregate_inspections(self, date_from, date_to):
        self.inspection_dates = (date_from, date_to)
        return self.inspections

    def find_aggregate_defects_for_lots(self, lot_ids):
        return self.find_defects_for_lots(lot_ids)

    def find_defects_between(self, date_from, date_to):
        self.defect_dates = (date_from, date_to)
        return self.records

    def find_product_master_for_parts(self, part_numbers):
        return [item for item in self.masters if item.product_number in part_numbers]

    def find_qr_history_lots(self, date_from, date_to):
        self.qr_dates = (date_from, date_to)
        return [QrHistoryItem(lot_id=lot) for lot in self.qr_lots]

    def find_defects_for_lots(self, lot_ids):
        self.requested_lots = set(lot_ids)
        return [item for item in self.records if item.lot_id in lot_ids]


class ReportBusinessRulesTests(unittest.TestCase):
    def test_summary_uses_total_quantity_instead_of_average_row_rates(self):
        service = DefectService(None)
        result = service.build_search_result(pd.DataFrame([
            {"号機": "1", "数量": 10, "総不具合数": 5, "不良率": 0.5},
            {"号機": "2", "数量": 90, "総不具合数": 9, "不良率": 0.1},
        ]), None)
        self.assertEqual(result.summary["quantity"], 100)
        self.assertEqual(result.summary["defect_count"], 14)
        self.assertAlmostEqual(result.summary["defect_rate"], 0.14)
        filtered = service.build_search_result(result.all_details, "2")
        self.assertEqual(len(filtered.details), 1)
        self.assertAlmostEqual(filtered.summary["defect_rate"], 0.1)
        self.assertEqual(result.machines, ["全て", "1", "2"])

    def test_zero_quantity_has_no_rate_and_empty_details_have_no_summary(self):
        service = DefectService(None)
        result = service.build_search_result(pd.DataFrame([
            {"数量": 0, "総不具合数": 2, "外観キズ": 0},
        ]), None)
        self.assertIsNone(result.summary["defect_rate"])
        self.assertIsNone(result.summary["外観キズ"])
        empty = service.build_search_result(pd.DataFrame(), None)
        self.assertEqual(empty.summary, {})
        self.assertEqual(empty.machines, ["全て"])

    def test_aggregate_excludes_chips_non_p_lots_and_nonpositive_value(self):
        repository = ReportRepository(
            [record("P001", "A", 10, 3), record("P002", "A", 3, 3),
             record("X003", "A", 10, 0), record("P004", "FREE", 4, 0),
             record("P005", "MISSING", 4, 0)],
            [ProductMasterItem("A", unit_price=5, product_weight=2),
             ProductMasterItem("FREE", unit_price=0, product_weight=2)],
        )
        start, end = date(2026, 1, 1), date(2026, 1, 31)
        output = DefectService(repository).export_aggregate(start, end)
        self.assertEqual(repository.inspection_dates, (date(2025, 10, 1), date(2026, 9, 30)))
        self.assertEqual(output["生産ロットID"].tolist(), ["P001"])
        row = output.iloc[0]
        self.assertEqual(row["廃棄不具合数"], 7)
        self.assertEqual(row["廃棄量"], 14)
        self.assertEqual(row["廃棄金額"], 35)

    def test_disposal_uses_qr_lots_and_keeps_zero_or_missing_master_value(self):
        repository = ReportRepository(
            [record("P001", "A", 10, 3), record("P002", "FREE", 4, 0),
             record("P003", "MISSING", 4, 0), record("P004", "A", 9, 0),
             record("X005", "A", 9, 0)],
            [ProductMasterItem("A", unit_price=5, product_weight=2),
             ProductMasterItem("FREE", unit_price=0, product_weight=2)],
            qr_lots=["P001", "P002", "P003", "X005"],
        )
        # The defect instruction date is outside this range: disposal selects QR lots.
        start, end = date(2026, 2, 1), date(2026, 2, 28)
        output = DefectService(repository).export_disposal(start, end)
        self.assertEqual(repository.qr_dates, (start, end))
        self.assertEqual(repository.requested_lots, {"P001", "P002", "P003", "X005"})
        by_lot = output.set_index("生産ロットID")
        self.assertEqual(set(by_lot.index), {"P001", "P002", "P003"})
        self.assertEqual(by_lot.loc["P001", "廃棄数"], 7)
        self.assertEqual(by_lot.loc["P001", "廃棄量"], 14)
        self.assertEqual(by_lot.loc["P001", "廃棄金額"], 35)
        self.assertEqual(by_lot.loc["P002", "廃棄金額"], 0)
        self.assertTrue(pd.isna(by_lot.loc["P003", "廃棄金額"]))

    def test_disposal_with_no_qr_lots_returns_empty(self):
        repository = ReportRepository([record("P001", "A", 3, 0)], [])
        result = DefectService(repository).export_disposal(date(2026, 1, 1), date(2026, 1, 31))
        self.assertTrue(result.empty)
        self.assertFalse(hasattr(repository, "requested_lots"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openpyxl import load_workbook

from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService

from tests.test_report_business_rules import ReportRepository, record
from defect_information_search.domain.models import ProductMasterItem


class ExportServiceTests(unittest.TestCase):
    def test_round_trip_preserves_columns_values_dates_and_nulls(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "result.xlsx"
            count = ExportService().export_rows(
                ["品番", "数量", "日時", "備考"],
                [("A001", 0, datetime(2026, 1, 2, 12, 30), None)],
                target,
            )
            self.assertEqual(count, 1)
            workbook = load_workbook(target)
            try:
                sheet = workbook["Sheet1"]
                self.assertEqual(list(sheet.values), [
                    ("品番", "数量", "日時", "備考"),
                    ("A001", 0, datetime(2026, 1, 2, 12, 30), None),
                ])
                self.assertEqual(sheet.freeze_panes, "A2")
                self.assertEqual(sheet.auto_filter.ref, "A1:D2")
            finally:
                workbook.close()

    def test_aggregate_service_columns_match_excel_format_positions(self):
        repository = ReportRepository(
            [record("P001", "A", 10, 3)],
            [ProductMasterItem("A", unit_price=5, product_weight=2)],
        )
        frame = DefectService(repository).export_aggregate(
            datetime(2026, 1, 1).date(), datetime(2026, 1, 31).date(),
        )
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "aggregate.xlsx"
            self.assertEqual(ExportService().export_dataframe(frame, target, "aggregate"), 1)
            workbook = load_workbook(target)
            try:
                sheet = workbook["Sheet1"]
                self.assertEqual(sheet["C1"].value, "検査日")
                self.assertEqual(sheet["D1"].value, "指示日")
                self.assertEqual(sheet["P1"].value, "廃棄量")
                self.assertEqual(sheet["Q1"].value, "廃棄金額")
                self.assertEqual(sheet["T1"].value, "不良率")
                self.assertEqual(sheet["P2"].value, 14)
                self.assertEqual(sheet["Q2"].value, 35)
                self.assertEqual(sheet["P2"].fill.fgColor.rgb, "00DAF2D0")
                self.assertEqual(sheet["Q2"].fill.fgColor.rgb, "00FBE2D5")
                self.assertEqual(sheet["T2"].number_format, "0.00%")
                self.assertIn("集計条件", workbook.sheetnames)
                for column in "FGHIJ":
                    self.assertTrue(sheet.column_dimensions[column].hidden)
            finally:
                workbook.close()

    def test_repeat_save_replaces_rows_and_preserves_other_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "result.xlsx"
            unrelated = Path(temporary) / "keep.txt"
            unrelated.write_text("unchanged", encoding="utf-8")
            exporter = ExportService()
            exporter.export_rows(["品番"], [("OLD1",), ("OLD2",)], target)
            self.assertEqual(exporter.export_rows(["品番"], [("NEW",)], target), 1)
            workbook = load_workbook(target)
            try:
                self.assertEqual(list(workbook["Sheet1"].values), [("品番",), ("NEW",)])
            finally:
                workbook.close()
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "unchanged")

    def test_zero_rows_creates_header_only_workbook(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "empty.xlsx"
            self.assertEqual(ExportService().export_rows(["品番"], [], target), 0)
            workbook = load_workbook(target)
            try:
                sheet = workbook["Sheet1"]
                self.assertEqual(list(sheet.values), [("品番",)])
                self.assertIsNone(sheet.auto_filter.ref)
            finally:
                workbook.close()


if __name__ == "__main__":
    unittest.main()

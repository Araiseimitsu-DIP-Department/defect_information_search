from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from datetime import date

from tests.test_report_business_rules import ReportRepository, record
from defect_information_search.domain.models import InspectionSummary, ProductMasterItem
from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService
from defect_information_search.webview.bridge import WebviewBridge
from openpyxl import load_workbook


class AggregateBridgeTests(unittest.TestCase):
    def test_cancel_and_bad_dates_do_not_query_or_write(self):
        service = Mock()
        exporter = Mock()
        bridge = WebviewBridge(service, exporter)
        bridge._choose_save_path = Mock(return_value=None)
        self.assertFalse(bridge.export_aggregate("invalid", "2026-01-31")["ok"])
        self.assertFalse(bridge.export_aggregate("2026-02-01", "2026-01-31")["ok"])
        self.assertTrue(bridge.export_aggregate("2026-01-01", "2026-01-31")["canceled"])
        service.export_aggregate.assert_not_called()
        exporter.export_dataframe.assert_not_called()

    def test_aggregate_success_exposes_diagnostics_and_saved_workbook(self):
        repo = ReportRepository([record("P1", "A", 3, 1)],
                                [ProductMasterItem("A", unit_price=5)],
                                inspections=[InspectionSummary(1, "P1", date(2026, 1, 2)),
                                             InspectionSummary(2, "P2", date(2026, 1, 2))])
        bridge = WebviewBridge(DefectService(repo), ExportService())
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "aggregate.xlsx"
            bridge._choose_save_path = Mock(return_value=path)
            result = bridge.export_aggregate("2026-01-01", "2026-01-31")
            self.assertTrue(result["ok"])
            self.assertIn("未照合: 1ロット", result["notice"])
            workbook = load_workbook(path)
            try:
                self.assertEqual(workbook["Sheet1"]["Q2"].value, 10)
                notes = dict(list(workbook["集計条件"].values)[1:])
                self.assertEqual(notes["不具合情報未照合ロット数"], 1)
            finally:
                workbook.close()

    def test_failure_before_export_leaves_existing_file_unchanged(self):
        service = Mock()
        service.export_aggregate.side_effect = RuntimeError("inspection source unavailable")
        exporter = Mock()
        bridge = WebviewBridge(service, exporter)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "aggregate.xlsx"
            path.write_bytes(b"existing report")
            bridge._choose_save_path = Mock(return_value=path)
            self.assertFalse(bridge.export_aggregate("2026-01-01", "2026-01-31")["ok"])
            self.assertEqual(path.read_bytes(), b"existing report")
            exporter.export_dataframe.assert_not_called()

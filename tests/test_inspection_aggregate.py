from datetime import date
from dataclasses import replace
import unittest

from tests.test_report_business_rules import ReportRepository, record
from defect_information_search.domain.models import InspectionSummary, ProductMasterItem
from defect_information_search.services.defect_service import DefectService


class InspectionAggregateTests(unittest.TestCase):
    def build(self, inspections, records=None, price=5, start=date(2025, 10, 1), end=date(2026, 9, 30)):
        repo = ReportRepository(records or [record("P1", "A", 3, 1)],
                                [ProductMasterItem("A", unit_price=price, product_weight=2)],
                                inspections=inspections)
        return DefectService(repo).export_aggregate(start, end)

    def test_inspection_date_includes_record_with_instruction_outside_period(self):
        item = replace(record("P1", "A", 3, 1), instruction_date=date(2024, 1, 1))
        output = self.build([InspectionSummary(1, " P1 ", date(2025, 10, 2), quantity=50)], [item])
        self.assertEqual(output.iloc[0]["検査日"], date(2025, 10, 2))
        self.assertEqual(output.iloc[0]["指示日"], date(2024, 1, 1))
        self.assertEqual(output.iloc[0]["数量"], 50)
        self.assertAlmostEqual(output.iloc[0]["不良率"], 3/50)

    def test_first_inspection_in_each_term_and_archive_are_used(self):
        output = self.build([
            InspectionSummary(1, "P1", date(2025, 10, 2)),
            InspectionSummary(2, "P1", date(2025, 9, 30), 1),
            InspectionSummary(3, "P1", date(2025, 10, 1)),
        ], start=date(2024, 10, 1))
        self.assertEqual(output["検査日"].tolist(), [date(2025, 9, 30), date(2025, 10, 1)])
        self.assertEqual(output["廃棄金額"].tolist(), [10, 10])

    def test_monthly_export_does_not_recount_a_lot_first_inspected_earlier(self):
        output = self.build([InspectionSummary(1, "P1", date(2025, 10, 1)),
                             InspectionSummary(2, "P1", date(2026, 1, 1))],
                            start=date(2026, 1, 1), end=date(2026, 1, 31))
        self.assertTrue(output.empty)

    def test_same_day_current_has_priority_over_archive(self):
        output = self.build([InspectionSummary(1, "P1", date(2025, 10, 1), 1, quantity=80),
                             InspectionSummary(9, "P1", date(2025, 10, 1), 0, quantity=100)])
        self.assertEqual(output.iloc[0]["数量"], 100)
        self.assertEqual(len(output), 1)

    def test_defects_use_first_id_not_sum_or_latest(self):
        output = self.build([InspectionSummary(1, "P1", date(2025, 10, 1))],
                            [replace(record("P1", "A", 14, 0), record_id=20),
                             replace(record("P1", "A", 41, 0), record_id=10)])
        self.assertEqual(output.iloc[0]["廃棄不具合数"], 41)
        self.assertEqual(output.attrs["aggregate_info"]["重複不具合除外数"], 1)

    def test_half_even_rounding_is_allocated_by_product_and_day(self):
        output = self.build([InspectionSummary(1, "P1", date(2025, 10, 1)),
                             InspectionSummary(2, "P2", date(2025, 10, 1))],
                            [record("P1", "A", 2, 1), record("P2", "A", 2, 1)], price=1.5)
        self.assertEqual(output["廃棄金額"].tolist(), [2, 1])
        self.assertEqual(output["廃棄金額"].sum(), 3)

    def test_zero_allocated_amount_is_excluded_and_missing_data_is_counted(self):
        output = self.build([InspectionSummary(1, "P1", date(2025, 10, 1)),
                             InspectionSummary(2, "P2", date(2025, 10, 1))], price=0.1)
        self.assertTrue(output.empty)
        self.assertEqual(output.attrs["aggregate_info"]["不具合情報未照合ロット数"], 1)
        missing_price = self.build([InspectionSummary(1, "P1", date(2025, 10, 1))], price=None)
        self.assertEqual(missing_price.attrs["aggregate_info"]["単価未登録ロット数"], 1)

    def test_missing_or_invalid_inspection_never_falls_back_to_instruction(self):
        output = self.build([InspectionSummary(1, "P1", None),
                             InspectionSummary(2, "X1", date(2025, 10, 1))])
        self.assertTrue(output.empty)


if __name__ == "__main__":
    unittest.main()

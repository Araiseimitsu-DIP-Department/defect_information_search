from __future__ import annotations

import unittest
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.infrastructure.mappers.domain_mappers import (
    defect_records_frame_from_items,
    defect_records_from_frame,
    product_catalog_frame_from_items,
    product_catalog_items_from_frame,
    product_master_frame_from_items,
    product_master_items_from_frame,
    qr_history_frame_from_items,
    qr_history_items_from_frame,
)


class DomainMapperTests(unittest.TestCase):
    def test_product_catalog_items_from_frame(self) -> None:
        frame = pd.DataFrame(
            [
                {"品番": "P001", "品名": "部品A", "客先": "顧客A"},
                {"品番": "P002", "品名": None, "客先": "顧客B"},
            ]
        )

        items = product_catalog_items_from_frame(frame)

        self.assertEqual(items[0].part_number, "P001")
        self.assertEqual(items[0].part_name, "部品A")
        self.assertEqual(items[0].customer, "顧客A")
        self.assertEqual(items[1].part_name, None)

    def test_product_catalog_frame_from_items(self) -> None:
        frame = product_catalog_frame_from_items(
            [
                type("Item", (), {"part_number": "P001", "part_name": "部品A", "customer": "顧客A"})(),
                type("Item", (), {"part_number": "P002", "part_name": None, "customer": None})(),
            ]
        )

        self.assertEqual(list(frame["品番"]), ["P001", "P002"])
        self.assertEqual(frame.iloc[0]["品名"], "部品A")

    def test_product_master_items_from_frame(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "製品番号": "A001",
                    "製品名": "製品A",
                    "客先名": "顧客A",
                    "材質": "SUS",
                    "単価": 120.5,
                    "製品単重": 2.4,
                    "材料識別": 1,
                    "次工程": "加工",
                }
            ]
        )

        items = product_master_items_from_frame(frame)

        self.assertEqual(items[0].product_number, "A001")
        self.assertEqual(items[0].unit_price, 120.5)
        self.assertEqual(items[0].product_weight, 2.4)
        self.assertEqual(items[0].material_identification, 1)

    def test_product_master_frame_from_items(self) -> None:
        frame = product_master_frame_from_items(
            [
                type(
                    "Item",
                    (),
                    {
                        "product_number": "A001",
                        "product_name": "製品A",
                        "customer_name": "顧客A",
                        "material": "SUS",
                        "unit_price": 120.5,
                        "product_weight": 2.4,
                        "material_identification": 1,
                        "next_process": "加工",
                    },
                )()
            ]
        )

        self.assertEqual(frame.iloc[0]["製品番号"], "A001")
        self.assertEqual(frame.iloc[0]["製品単重"], 2.4)

    def test_qr_history_items_from_frame(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "生産ロットID": "P123",
                    "QRコード": "QR-001",
                    "日付時刻": "2026-04-14 12:30:00",
                    "日付": "2026-04-14",
                    "工程コード": "03",
                    "工程名": "検査",
                    "数量": 15,
                    "更新フラグ": "1",
                }
            ]
        )

        items = qr_history_items_from_frame(frame)

        self.assertEqual(items[0].lot_id, "P123")
        self.assertEqual(items[0].process_code, "03")
        self.assertEqual(items[0].quantity, 15)
        self.assertEqual(items[0].update_flag, "1")

    def test_qr_history_frame_from_items(self) -> None:
        frame = qr_history_frame_from_items(
            [
                type(
                    "Item",
                    (),
                    {
                        "lot_id": "P123",
                        "qr_code": "QR-001",
                        "recorded_at": None,
                        "operation_date": None,
                        "process_code": "03",
                        "process_name": "検査",
                        "quantity": 15,
                        "update_flag": "1",
                    },
                )()
            ]
        )

        self.assertEqual(frame.iloc[0]["生産ロットID"], "P123")
        self.assertEqual(frame.iloc[0]["数量"], 15)

    def test_defect_records_from_frame(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "ID": 1,
                    "生産ロットID": "P123",
                    "品番": "A001",
                    "指示日": "2026-04-14",
                    "号機": "1",
                    "検査者1": "山田",
                    "数量": 100,
                    "総不具合数": 3,
                    "不良率": 0.03,
                    "外観キズ": 1,
                    "切粉": 2,
                    "その他内容": "備考",
                }
            ]
        )

        items = defect_records_from_frame(frame)

        self.assertEqual(items[0].record_id, 1)
        self.assertEqual(items[0].lot_id, "P123")
        self.assertEqual(items[0].part_number, "A001")
        self.assertEqual(items[0].quantity, 100)
        self.assertEqual(items[0].total_defects, 3)
        self.assertEqual(items[0].defect_counts["外観キズ"], 1)
        self.assertEqual(items[0].defect_counts["切粉"], 2)

    def test_defect_records_frame_from_items(self) -> None:
        frame = defect_records_frame_from_items(
            [
                type(
                    "Item",
                    (),
                    {
                        "record_id": 1,
                        "lot_id": "P123",
                        "part_number": "A001",
                        "instruction_date": None,
                        "machine_code": "1",
                        "inspector_names": ("山田", None, None, None, None),
                        "quantity": 100,
                        "total_defects": 3,
                        "defect_rate": 0.03,
                        "defect_counts": {"外観キズ": 1, "切粉": 2},
                        "other_content": "備考",
                    },
                )()
            ]
        )

        self.assertEqual(frame.iloc[0]["ID"], 1)
        self.assertEqual(frame.iloc[0]["外観キズ"], 1)
        self.assertEqual(frame.iloc[0]["切粉"], 2)


if __name__ == "__main__":
    unittest.main()

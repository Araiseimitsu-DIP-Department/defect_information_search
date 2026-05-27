from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from defect_information_search.domain.models import (
    DefectRecord,
    ProductCatalogItem,
    ProductMasterItem,
    QrHistoryItem,
)


def product_catalog_items_from_frame(frame: pd.DataFrame) -> list[ProductCatalogItem]:
    items: list[ProductCatalogItem] = []
    for row in frame.to_dict("records"):
        items.append(
            ProductCatalogItem(
                part_number=_as_optional_str(_value(row, "part_number", "品番")) or "",
                part_name=_as_optional_str(_value(row, "part_name", "品名")),
                customer=_as_optional_str(_value(row, "customer_name", "客先")),
            )
        )
    return items


def product_catalog_frame_from_items(items: list[ProductCatalogItem]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "品番": item.part_number,
                "品名": item.part_name,
                "客先": item.customer,
            }
            for item in items
        ],
        columns=["品番", "品名", "客先"],
    )


def product_master_items_from_frame(frame: pd.DataFrame) -> list[ProductMasterItem]:
    items: list[ProductMasterItem] = []
    for row in frame.to_dict("records"):
        items.append(
            ProductMasterItem(
                product_number=_as_optional_str(_value(row, "product_number", "製品番号")) or "",
                product_name=_as_optional_str(_value(row, "product_name", "製品名")),
                customer_name=_as_optional_str(_value(row, "customer_name", "客先名")),
                material=_as_optional_str(_value(row, "material", "材質")),
                unit_price=_as_optional_float(_value(row, "unit_price", "単価")),
                product_weight=_as_optional_float(_value(row, "unit_weight", "製品単重")),
                material_identification=_as_optional_int(_value(row, "material_type", "材料識別")),
                next_process=_as_optional_str(_value(row, "next_process", "次工程")),
            )
        )
    return items


def product_master_frame_from_items(items: list[ProductMasterItem]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "製品番号": item.product_number,
                "製品名": item.product_name,
                "客先名": item.customer_name,
                "材質": item.material,
                "単価": item.unit_price,
                "製品単重": item.product_weight,
                "材料識別": item.material_identification,
                "次工程": item.next_process,
            }
            for item in items
        ],
        columns=["製品番号", "製品名", "客先名", "材質", "単価", "製品単重", "材料識別", "次工程"],
    )


def qr_history_items_from_frame(frame: pd.DataFrame) -> list[QrHistoryItem]:
    items: list[QrHistoryItem] = []
    for row in frame.to_dict("records"):
        items.append(
            QrHistoryItem(
                lot_id=_as_optional_str(_value(row, "production_lot_id", "生産ロットID")) or "",
                qr_code=_as_optional_str(_value(row, "qr_code", "QRコード")),
                recorded_at=_as_optional_datetime(_value(row, "recorded_at", "日付時刻")),
                operation_date=_as_optional_date(_value(row, "event_at", "日付")),
                process_code=_as_optional_str(_value(row, "process_code", "工程コード")),
                process_name=_as_optional_str(_value(row, "process_name", "工程名")),
                quantity=_as_optional_int(_value(row, "quantity", "数量")),
                update_flag=_as_optional_str(_value(row, "updated_flag", "更新フラグ")),
            )
        )
    return items


def qr_history_frame_from_items(items: list[QrHistoryItem]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "生産ロットID": item.lot_id,
                "QRコード": item.qr_code,
                "日付時刻": item.recorded_at,
                "日付": item.operation_date,
                "工程コード": item.process_code,
                "工程名": item.process_name,
                "数量": item.quantity,
                "更新フラグ": item.update_flag,
            }
            for item in items
        ],
        columns=["生産ロットID", "QRコード", "日付時刻", "日付", "工程コード", "工程名", "数量", "更新フラグ"],
    )


def defect_records_from_frame(frame: pd.DataFrame) -> list[DefectRecord]:
    items: list[DefectRecord] = []
    for row in frame.to_dict("records"):
        defect_counts = {
            label: _as_optional_int(_value(row, english, label)) or 0
            for label, english in DEFECT_COLUMN_PAIRS
        }
        items.append(
            DefectRecord(
                record_id=_as_optional_int(_value(row, "id", "ID")),
                lot_id=_as_optional_str(_value(row, "production_lot_id", "生産ロットID")) or "",
                part_number=_as_optional_str(_value(row, "part_number", "品番")) or "",
                instruction_date=_as_optional_date(_value(row, "instruction_date", "指示日")),
                machine_code=_as_optional_str(_value(row, "machine_no", "号機")),
                inspector_names=tuple(
                    _as_optional_str(_value(row, f"inspector_{index}", f"検査者{index}"))
                    for index in range(1, 6)
                ),  # type: ignore[arg-type]
                quantity=_as_optional_int(_value(row, "quantity", "数量")),
                work_minutes=_as_optional_int(_value(row, "work_minutes", "時間")),
                total_defects=_as_optional_int(_value(row, "total_defect_count", "総不具合数")),
                defect_rate=_as_optional_float(_value(row, "defect_rate", "不良率")),
                defect_counts=defect_counts,
                other_content=_as_optional_str(_value(row, "other_detail", "その他内容")),
                numeric_inspector=_as_optional_str(_value(row, "inspector_name", "数値検査員")),
            )
        )
    return items


def defect_records_frame_from_items(items: list[DefectRecord]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    inspector_columns = ["検査者1", "検査者2", "検査者3", "検査者4", "検査者5"]
    defect_columns = [
        "外観キズ",
        "圧痕",
        "切粉",
        "毟れ",
        "穴大",
        "穴小",
        "穴キズ",
        "バリ",
        "短寸",
        "面粗",
        "サビ",
        "ボケ",
        "挽目",
        "汚れ",
        "メッキ",
        "落下",
        "フクレ",
        "ツブレ",
        "ボッチ",
        "段差",
        "バレル石",
        "径プラス",
        "径マイナス",
        "ゲージ",
        "異物混入",
        "形状不良",
        "こすれ",
        "変色シミ",
        "材料キズ",
        "ゴミ",
        "その他",
    ]
    for item in items:
        row: dict[str, object] = {
            "ID": item.record_id,
            "生産ロットID": item.lot_id,
            "品番": item.part_number,
            "指示日": item.instruction_date,
            "号機": item.machine_code,
            "時間": item.work_minutes,
            "数量": item.quantity,
            "総不具合数": item.total_defects,
            "不良率": item.defect_rate,
            "その他内容": item.other_content,
            "数値検査員": item.numeric_inspector,
        }
        for name, value in zip(inspector_columns, item.inspector_names):
            row[name] = value
        for name in defect_columns:
            row[name] = item.defect_counts.get(name, 0)
        rows.append(row)
    columns = [
        "ID",
        "生産ロットID",
        "品番",
        "指示日",
        "号機",
        "検査者1",
        "検査者2",
        "検査者3",
        "検査者4",
        "検査者5",
        "時間",
        "数量",
        "総不具合数",
        "不良率",
    ] + defect_columns + ["その他内容", "数値検査員"]
    return pd.DataFrame(rows, columns=columns)


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    text = str(value).strip()
    return text or None


DEFECT_COLUMN_PAIRS = [
    ("外観キズ", "appearance_scratch"),
    ("圧痕", "dent"),
    ("切粉", "chip"),
    ("毟れ", "tear"),
    ("穴大", "hole_large"),
    ("穴小", "hole_small"),
    ("穴キズ", "hole_scratch"),
    ("バリ", "burr"),
    ("短寸", "short_length"),
    ("面粗", "rough_surface"),
    ("サビ", "rust"),
    ("ボケ", "blur"),
    ("挽目", "turning_mark"),
    ("汚れ", "stain"),
    ("メッキ", "plating"),
    ("落下", "drop_damage"),
    ("フクレ", "blister"),
    ("ツブレ", "crush"),
    ("ボッチ", "projection"),
    ("段差", "step"),
    ("バレル石", "barrel_stone"),
    ("径プラス", "diameter_plus"),
    ("径マイナス", "diameter_minus"),
    ("ゲージ", "gauge"),
    ("異物混入", "foreign_matter"),
    ("形状不良", "shape_defect"),
    ("こすれ", "rub_mark"),
    ("変色シミ", "discoloration"),
    ("材料キズ", "material_scratch"),
    ("ゴミ", "dust"),
    ("その他", "other"),
]


def _value(row: dict[str, object], *names: str) -> object:
    for name in names:
        if name in row:
            return row.get(name)
    return None


def _as_optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_optional_date(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _as_optional_datetime(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None

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
                part_number=_as_optional_str(row.get("品番")) or "",
                part_name=_as_optional_str(row.get("品名")),
                customer=_as_optional_str(row.get("客先")),
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
                product_number=_as_optional_str(row.get("製品番号")) or "",
                product_name=_as_optional_str(row.get("製品名")),
                customer_name=_as_optional_str(row.get("客先名")),
                material=_as_optional_str(row.get("材質")),
                unit_price=_as_optional_float(row.get("単価")),
                product_weight=_as_optional_float(row.get("製品単重")),
                material_identification=_as_optional_int(row.get("材料識別")),
                next_process=_as_optional_str(row.get("次工程")),
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
                lot_id=_as_optional_str(row.get("生産ロットID")) or "",
                qr_code=_as_optional_str(row.get("QRコード")),
                recorded_at=_as_optional_datetime(row.get("日付時刻")),
                operation_date=_as_optional_date(row.get("日付")),
                process_code=_as_optional_str(row.get("工程コード")),
                process_name=_as_optional_str(row.get("工程名")),
                quantity=_as_optional_int(row.get("数量")),
                update_flag=_as_optional_str(row.get("更新フラグ")),
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
    for row in frame.to_dict("records"):
        defect_counts = {name: _as_optional_int(row.get(name)) or 0 for name in defect_columns}
        items.append(
            DefectRecord(
                record_id=_as_optional_int(row.get("ID")),
                lot_id=_as_optional_str(row.get("生産ロットID")) or "",
                part_number=_as_optional_str(row.get("品番")) or "",
                instruction_date=_as_optional_date(row.get("指示日")),
                machine_code=_as_optional_str(row.get("号機")),
                inspector_names=tuple(_as_optional_str(row.get(name)) for name in inspector_columns),  # type: ignore[arg-type]
                quantity=_as_optional_int(row.get("数量")),
                total_defects=_as_optional_int(row.get("総不具合数")),
                defect_rate=_as_optional_float(row.get("不良率")),
                defect_counts=defect_counts,
                other_content=_as_optional_str(row.get("その他内容")),
                numeric_inspector=_as_optional_str(row.get("数値検査員")),
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
            "時間": None,
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

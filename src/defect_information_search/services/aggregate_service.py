from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

import pandas as pd

from defect_information_search.application.ports.defect_repository import DefectRepository
from defect_information_search.infrastructure.mappers.domain_mappers import defect_records_frame_from_items
from defect_information_search.models import DEFECT_FIELDS


def fiscal_start(day: date) -> date:
    return date(day.year if day.month >= 10 else day.year - 1, 10, 1)


def build_aggregate(repository: DefectRepository, date_from: date, date_to: date) -> pd.DataFrame:
    if date_from > date_to:
        raise ValueError("開始日と終了日の指定が正しくありません。")
    # Choose the first inspection within each full fiscal year, then filter the requested dates.
    # Monthly exports therefore partition the same fiscal-year totals.
    year_start = fiscal_start(date_from)
    year_end = date(fiscal_start(date_to).year + 1, 9, 30)
    inspections = sorted(repository.find_aggregate_inspections(year_start, year_end), key=lambda item: (
        item.inspection_date or date.max, item.source_priority,
        item.record_id if item.record_id is not None else float("inf"),
    ))
    selected = {}
    duplicate_inspections = 0
    for item in inspections:
        lot = item.lot_id.strip()
        day = item.inspection_date
        if not lot.startswith("P") or day is None or not year_start <= day <= year_end:
            continue
        key = (fiscal_start(day), lot)
        if key in selected:
            duplicate_inspections += 1
        else:
            selected[key] = item
    lots = sorted({item.lot_id.strip() for item in selected.values()})
    defects = sorted(repository.find_aggregate_defects_for_lots(lots), key=lambda item:
                     item.record_id if item.record_id is not None else float("inf"))
    first_defects = {}
    duplicate_defects = 0
    for item in defects:
        lot = item.lot_id.strip()
        if lot in first_defects:
            duplicate_defects += 1
        else:
            first_defects[lot] = item
    parts = sorted({item.part_number.strip() for item in first_defects.values()}
                   | {item.part_number.strip() for item in selected.values()})
    masters = {}
    for item in repository.find_product_master_for_parts(parts):
        masters.setdefault(item.product_number.strip(), item)
    info = {
        "日付基準": "検査日（各期10/1～翌9/30の初回、通常・保存を統合）",
        "対象期間": f"{date_from.isoformat()} ～ {date_to.isoformat()}",
        "金額算出": "（総不具合数－切粉）×現在単価。品番・検査日単位で1円に丸め、端数がちょうど0.5円の場合は偶数円へ丸めます。金額を各ロットへ配分した参考値です。",
        "対象条件": "Pロット、廃棄不具合数>0、配分後の廃棄金額>0。不具合はID順の先頭1件。",
        "不具合情報未照合ロット数": 0,
        "単価未登録ロット数": 0,
        "期内の重複検査除外数": duplicate_inspections,
        "重複不具合除外数": duplicate_defects,
    }
    available_dates = [item.inspection_date for item in inspections if item.inspection_date is not None]
    info["取得した検査記録の最小日"] = min(available_dates).isoformat() if available_dates else "記録なし"
    info["取得した検査記録の最大日"] = max(available_dates).isoformat() if available_dates else "記録なし"
    info["取得範囲の注意"] = "取得日はデータの存在範囲です。対象期間全体の記録が揃っている保証ではありません。"
    counts, amounts = {}, {}
    rows = []
    # Allocation must use the full fiscal-year selection before filtering a subperiod.
    mapped_rows = dict(zip(first_defects, defect_records_frame_from_items(list(first_defects.values())).to_dict("records")))
    for inspection in selected.values():
        lot, day = inspection.lot_id.strip(), inspection.inspection_date
        item = first_defects.get(lot)
        in_range = date_from <= day <= date_to
        if item is None:
            if in_range:
                info["不具合情報未照合ロット数"] += 1
            continue
        disposal_count = (item.total_defects or 0) - item.defect_counts.get("切粉", 0)
        if disposal_count <= 0:
            continue
        part = item.part_number.strip() or inspection.part_number.strip()
        master = masters.get(part)
        try:
            price = Decimal(str(master.unit_price)) if master else Decimal("NaN")
        except (InvalidOperation, ValueError):
            price = Decimal("NaN")
        if not price.is_finite() or price <= 0:
            if in_range:
                info["単価未登録ロット数"] += 1
            continue
        key = (day, part)
        counts[key] = counts.get(key, 0) + disposal_count
        cumulative = int((Decimal(counts[key]) * price).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
        amount = cumulative - amounts.get(key, 0)
        amounts[key] = cumulative
        if not in_range or amount <= 0:
            continue
        row = mapped_rows[lot].copy()
        quantity = inspection.quantity if inspection.quantity is not None else item.quantity
        row.update({"生産ロットID": lot, "品番": part, "検査日": day,
                    "数量": quantity,
                    "不良率": (item.total_defects or 0) / quantity if quantity else None,
                    "単価": float(price), "製品単重": master.product_weight,
                    "材質": master.material, "廃棄不具合数": disposal_count,
                    "廃棄量": disposal_count * master.product_weight if master.product_weight is not None else None,
                    "廃棄金額": amount})
        rows.append(row)
    columns = ["生産ロットID", "品番", "検査日", "指示日", "号機",
               *[f"検査者{i}" for i in range(1, 6)], "時間", "数量", "製品単重", "材質", "単価",
               "廃棄量", "廃棄金額", "廃棄不具合数", "総不具合数", "不良率",
               *[label for label, _ in DEFECT_FIELDS], "その他内容"]
    frame = pd.DataFrame(rows, columns=columns).sort_values(["品番", "検査日", "生産ロットID"], kind="stable").reset_index(drop=True)
    info["出力行数"] = len(frame)
    frame.attrs["aggregate_info"] = info
    return frame

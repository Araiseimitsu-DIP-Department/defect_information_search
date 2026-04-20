from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class ProductCatalogItem:
    part_number: str
    part_name: str | None = None
    customer: str | None = None


@dataclass(frozen=True, slots=True)
class ProductMasterItem:
    product_number: str
    product_name: str | None = None
    customer_name: str | None = None
    material: str | None = None
    unit_price: float | None = None
    product_weight: float | None = None
    material_identification: int | None = None
    next_process: str | None = None


@dataclass(frozen=True, slots=True)
class QrHistoryItem:
    lot_id: str
    qr_code: str | None = None
    recorded_at: datetime | None = None
    operation_date: date | None = None
    process_code: str | None = None
    process_name: str | None = None
    quantity: int | None = None
    update_flag: str | None = None


@dataclass(frozen=True, slots=True)
class InspectorMasterItem:
    inspector_id: str
    inspector_name: str | None = None
    category: str | None = None
    visible: bool = True


@dataclass(frozen=True, slots=True)
class InspectionRecord:
    record_id: int | None
    recorded_at: datetime | None
    lot_id: str
    inspector_id: str | None = None
    process_name: str | None = None
    machine_code: str | None = None


@dataclass(frozen=True, slots=True)
class DefectRecord:
    record_id: int | None
    lot_id: str
    part_number: str
    instruction_date: date | None = None
    machine_code: str | None = None
    inspector_names: tuple[str | None, str | None, str | None, str | None, str | None] = field(
        default_factory=lambda: (None, None, None, None, None)
    )
    quantity: int | None = None
    total_defects: int | None = None
    defect_rate: float | None = None
    defect_counts: dict[str, int] = field(default_factory=dict)
    other_content: str | None = None
    numeric_inspector: str | None = None

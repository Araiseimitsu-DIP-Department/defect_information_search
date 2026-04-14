from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date
from typing import Protocol

from defect_information_search.domain.models import (
    DefectRecord,
    ProductCatalogItem,
    ProductMasterItem,
    QrHistoryItem,
)


class DefectRepository(Protocol):
    def find_products(self, keyword: str) -> Sequence[ProductCatalogItem]:
        ...

    def find_defects_for_part(self, part_number: str, date_from: date, date_to: date) -> Sequence[DefectRecord]:
        ...

    def find_defects_between(self, date_from: date, date_to: date | None = None) -> Sequence[DefectRecord]:
        ...

    def find_qr_history_lots(self, date_from: date, date_to: date) -> Sequence[QrHistoryItem]:
        ...

    def find_defects_for_lots(self, lot_ids: Sequence[str]) -> Sequence[DefectRecord]:
        ...

    def find_product_master_for_parts(self, part_numbers: Sequence[str]) -> Sequence[ProductMasterItem]:
        ...

    def iter_all_defects(self, date_from: date, date_to: date) -> tuple[Sequence[str], Iterable[Sequence[object]]]:
        ...

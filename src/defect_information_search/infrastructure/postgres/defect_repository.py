from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

from defect_information_search.application.ports.defect_repository import DefectRepository
from defect_information_search.domain.models import DefectRecord, ProductCatalogItem, ProductMasterItem, QrHistoryItem


class PostgresDefectRepository(DefectRepository):
    """Placeholder for the future PostgreSQL implementation.

    The interface is already fixed so the UI and application layer can stay unchanged
    when the backend is swapped.
    """

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn

    def find_products(self, keyword: str) -> Sequence[ProductCatalogItem]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

    def find_defects_for_part(self, part_number: str, date_from: date, date_to: date) -> Sequence[DefectRecord]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

    def find_defects_between(self, date_from: date, date_to: date | None = None) -> Sequence[DefectRecord]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

    def find_qr_history_lots(self, date_from: date, date_to: date) -> Sequence[QrHistoryItem]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

    def find_defects_for_lots(self, lot_ids: Sequence[str]) -> Sequence[DefectRecord]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

    def find_product_master_for_parts(self, part_numbers: Sequence[str]) -> Sequence[ProductMasterItem]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

    def iter_all_defects(self, date_from: date, date_to: date) -> tuple[Sequence[str], Iterable[Sequence[object]]]:  # pragma: no cover - placeholder
        raise NotImplementedError("PostgreSQL repository is not implemented yet.")

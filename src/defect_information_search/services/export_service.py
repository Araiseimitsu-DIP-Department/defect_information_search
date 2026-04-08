from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill


class ExportService:
    def export_dataframe(
        self,
        dataframe: pd.DataFrame,
        target_path: Path,
        formatter: str | None = None,
    ) -> None:
        dataframe.to_excel(target_path, index=False)
        if formatter == "aggregate":
            self._format_aggregate_sheet(target_path)
        elif formatter == "disposal":
            self._autofit(target_path)

    def _format_aggregate_sheet(self, path: Path) -> None:
        workbook = load_workbook(path)
        sheet = workbook.active
        sheet.auto_filter.ref = sheet.dimensions
        sheet.freeze_panes = "A2"
        for column_letter in ["E", "F", "G", "H", "I"]:
            sheet.column_dimensions[column_letter].hidden = True
        green_fill = PatternFill(fill_type="solid", fgColor="DAF2D0")
        orange_fill = PatternFill(fill_type="solid", fgColor="FBE2D5")
        for cell in sheet["O"]:
            cell.fill = green_fill
        for cell in sheet["P"]:
            cell.fill = orange_fill
        for cell in sheet["S"]:
            cell.number_format = "0.00%"
        self._autofit_sheet(sheet)
        workbook.save(path)

    def _autofit(self, path: Path) -> None:
        workbook = load_workbook(path)
        self._autofit_sheet(workbook.active)
        workbook.save(path)

    def _autofit_sheet(self, sheet) -> None:
        for column_cells in sheet.columns:
            length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(length + 3, 40)

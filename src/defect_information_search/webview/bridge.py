from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from defect_information_search.config import APP_NAME
from defect_information_search.models import DEFECT_FIELDS
from defect_information_search.services.defect_service import DETAIL_COLUMNS as SERVICE_DETAIL_COLUMNS
from defect_information_search.services.defect_service import DefectService, SearchResult
from defect_information_search.services.export_service import ExportService
from defect_information_search.shared.errors import RepositoryError


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _frame_to_payload(frame: pd.DataFrame) -> dict[str, Any]:
    clean = frame.copy()
    records = [{key: _json_safe(value) for key, value in row.items()} for row in clean.to_dict(orient="records")]
    return {
        "columns": list(clean.columns),
        "rows": records,
        "row_count": int(len(clean.index)),
    }


def _search_result_payload(result: SearchResult) -> dict[str, Any]:
    return {
        "all_details": _frame_to_payload(result.all_details),
        "summary": {key: _json_safe(value) for key, value in result.summary.items()},
        "details": _frame_to_payload(result.details),
        "machines": list(result.machines),
    }


class WebviewBridge:
    def __init__(self, service: DefectService, export_service: ExportService) -> None:
        self._service = service
        self._export_service = export_service
        self._window: Any = None

    def bind_window(self, window: Any) -> None:
        self._window = window

    def bootstrap(self) -> dict[str, Any]:
        today = date.today()
        default_from = _shift_years(today, -3)
        return {
            "ok": True,
            "app_name": APP_NAME,
            "default_search_from": default_from.isoformat(),
            "default_search_to": today.isoformat(),
            "defect_fields": [label for label, _ in DEFECT_FIELDS],
            "detail_columns": list(SERVICE_DETAIL_COLUMNS),
            "messages": {
                "empty_keyword": "品番を入力してください。",
                "no_products": "該当する品番はありません。",
            },
        }

    def search_products(self, keyword: str) -> dict[str, Any]:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return {"ok": False, "error": "品番を入力してください。"}

        try:
            products = self._service.find_products(normalized_keyword)
        except RepositoryError as exc:
            return {"ok": False, "error": "データベース検索に失敗しました。", "detail": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}

        frame = pd.DataFrame(products)
        return {"ok": True, "products": _frame_to_payload(frame)}

    def load_product(self, part_number: str, date_from: str, date_to: str) -> dict[str, Any]:
        start_date = self._parse_date(date_from)
        end_date = self._parse_date(date_to)
        if start_date is None or end_date is None:
            return {"ok": False, "error": "日付の形式が正しくありません。"}
        if start_date > end_date:
            return {"ok": False, "error": "開始日と終了日の指定が正しくありません。"}

        try:
            result = self._service.load_search_result(part_number, start_date, end_date, None)
        except RepositoryError as exc:
            return {"ok": False, "error": "データ取得に失敗しました。", "detail": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}

        return {"ok": True, "result": _search_result_payload(result)}

    def filter_by_machine(self, all_details: dict[str, Any], machine: str | None) -> dict[str, Any]:
        try:
            frame = self._payload_to_frame(all_details)
            result = self._service.build_search_result(frame, None if machine in {None, "", "全て"} else machine)
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "result": _search_result_payload(result)}

    def export_current(self, details_payload: dict[str, Any], default_name: str, formatter: str | None = None) -> dict[str, Any]:
        try:
            dataframe = self._payload_to_frame(details_payload)
            if dataframe.empty:
                return {"ok": False, "error": "出力できるデータがありません。"}
            target_path = self._choose_save_path(default_name)
            if target_path is None:
                return {"ok": True, "canceled": True}
            exported_rows = self._export_service.export_dataframe(dataframe, target_path, formatter=formatter)
        except RepositoryError as exc:
            return {"ok": False, "error": "エクスポートに失敗しました。", "detail": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}

        return {"ok": True, "path": str(target_path), "exported_rows": int(exported_rows)}

    def export_all_defects(self, date_from: str, date_to: str) -> dict[str, Any]:
        return self._export_by_dates(
            title="不具合情報エクスポート",
            default_name="不具合情報_全品番.xlsx",
            date_from=date_from,
            date_to=date_to,
            action=lambda target_path, start_date, end_date: self._service.export_all_defects_to_excel(
                self._export_service,
                target_path,
                start_date,
                end_date,
            ),
        )

    def export_aggregate(self, date_from: str, date_to: str) -> dict[str, Any]:
        start_date = self._parse_date(date_from)
        end_date = self._parse_date(date_to)
        if start_date is None or end_date is None:
            return {"ok": False, "error": "日付の形式が正しくありません。"}
        if start_date > end_date:
            return {"ok": False, "error": "開始日と終了日の指定が正しくありません。"}

        try:
            target_path = self._choose_save_path("集計データ.xlsx")
            if target_path is None:
                return {"ok": True, "canceled": True}
            dataframe = self._service.export_aggregate(start_date, end_date)
            if dataframe.empty:
                return {"ok": False, "error": "出力できるデータがありません。"}
            exported_rows = self._export_service.export_dataframe(dataframe, target_path, formatter="aggregate")
        except RepositoryError as exc:
            return {"ok": False, "error": "集計データに失敗しました。", "detail": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}

        if exported_rows == 0:
            return {"ok": False, "error": "出力できるデータがありません。"}
        return {"ok": True, "path": str(target_path), "exported_rows": int(exported_rows)}

    def export_disposal(self, date_from: str, date_to: str) -> dict[str, Any]:
        start_date = self._parse_date(date_from)
        end_date = self._parse_date(date_to)
        if start_date is None or end_date is None:
            return {"ok": False, "error": "日付の形式が正しくありません。"}
        if start_date > end_date:
            return {"ok": False, "error": "開始日と終了日の指定が正しくありません。"}

        try:
            target_path = self._choose_save_path("廃棄データ.xlsx")
            if target_path is None:
                return {"ok": True, "canceled": True}
            dataframe = self._service.export_disposal(start_date, end_date)
            if dataframe.empty:
                return {"ok": False, "error": "出力できるデータがありません。"}
            exported_rows = self._export_service.export_dataframe(dataframe, target_path, formatter="disposal")
        except RepositoryError as exc:
            return {"ok": False, "error": "廃棄データエクスポートに失敗しました。", "detail": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}

        if exported_rows == 0:
            return {"ok": False, "error": "出力できるデータがありません。"}
        return {"ok": True, "path": str(target_path), "exported_rows": int(exported_rows)}

    def _export_by_dates(
        self,
        *,
        title: str,
        default_name: str,
        date_from: str,
        date_to: str,
        action: Any,
    ) -> dict[str, Any]:
        start_date = self._parse_date(date_from)
        end_date = self._parse_date(date_to)
        if start_date is None or end_date is None:
            return {"ok": False, "error": "日付の形式が正しくありません。"}
        if start_date > end_date:
            return {"ok": False, "error": "開始日と終了日の指定が正しくありません。"}

        try:
            target_path = self._choose_save_path(default_name)
            if target_path is None:
                return {"ok": True, "canceled": True}
            exported_rows = action(target_path, start_date, end_date)
        except RepositoryError as exc:
            return {"ok": False, "error": f"{title}に失敗しました。", "detail": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge guard
            return {"ok": False, "error": str(exc)}

        if exported_rows == 0:
            return {"ok": False, "error": "出力できるデータがありません。"}
        return {"ok": True, "path": str(target_path), "exported_rows": int(exported_rows)}

    def _payload_to_frame(self, payload: dict[str, Any]) -> pd.DataFrame:
        columns = list(payload.get("columns") or [])
        rows = list(payload.get("rows") or [])
        if not rows:
            return pd.DataFrame(columns=columns)
        frame = pd.DataFrame(rows)
        if columns:
            return frame.reindex(columns=columns)
        return frame

    def _choose_save_path(self, default_name: str) -> Path | None:
        if self._window is None:
            return None

        import webview

        desktop = Path.home() / "Desktop"
        selected = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=str(desktop if desktop.exists() else Path.home()),
            save_filename=default_name,
        )
        if not selected:
            return None
        if isinstance(selected, (list, tuple)):
            selected = selected[0]
        return Path(selected)

    def _parse_date(self, value: str) -> date | None:
        try:
            return date.fromisoformat(value)
        except Exception:
            return None

    def close_app(self) -> dict[str, Any]:
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass
        return {"ok": True}


def _shift_years(value: date, years: int) -> date:
    target_year = value.year + years
    try:
        return value.replace(year=target_year)
    except ValueError:
        return value.replace(year=target_year, day=28)

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pythoncom
import pywintypes
import win32com.client


class AccessGatewayError(RuntimeError):
    """Access/DAO 読み取りに失敗した場合の例外。"""


@dataclass
class _OpenedDatabase:
    db: Any
    mode: str
    app: Any | None = None


class AccessSession:
    def __init__(self, gateway: AccessGateway) -> None:  # type: ignore[name-defined]
        self._gateway = gateway
        self._opened: _OpenedDatabase | None = None

    def __enter__(self) -> AccessSession:
        pythoncom.CoInitialize()
        self._opened = self._gateway._open_database()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self._opened is not None:
            self._gateway._close_database(self._opened)
            self._opened = None
        pythoncom.CoUninitialize()

    def fetch_all(self, sql: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
        if self._opened is None:
            raise AccessGatewayError("Access セッションが開始されていません。")
        rendered_sql = self._gateway._render_sql(sql, params or [])
        return self._gateway._fetch_all_from_db(self._opened.db, rendered_sql)

    def fetch_one(self, sql: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None


class AccessGateway:
    def __init__(self, access_db_path: Path) -> None:
        self.access_db_path = access_db_path
        self._normalized_db_path = self._normalize_path(access_db_path)

    def session(self) -> AccessSession:
        return AccessSession(self)

    def fetch_all(self, sql: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
        with self.session() as session:
            return session.fetch_all(sql, params)

    def fetch_one(self, sql: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
        with self.session() as session:
            return session.fetch_one(sql, params)

    def _open_database(self) -> _OpenedDatabase:
        errors: list[str] = []
        for opener in (self._open_via_active_access, self._open_via_dao, self._open_via_new_access_app):
            try:
                return opener()
            except Exception as exc:
                errors.append(f"{opener.__name__}: {exc}")
        raise AccessGatewayError("\n".join(errors))

    def _close_database(self, opened: _OpenedDatabase) -> None:
        if opened.mode == "dao":
            try:
                opened.db.Close()
            except Exception:
                pass
            return

        if opened.mode == "new_access" and opened.app is not None:
            try:
                opened.app.CloseCurrentDatabase()
            except Exception:
                pass
            try:
                opened.app.Quit()
            except Exception:
                pass

    def _open_via_active_access(self) -> _OpenedDatabase:
        app = win32com.client.GetActiveObject("Access.Application")
        current_path = getattr(app.CurrentProject, "FullName", "")
        if self._normalize_path(Path(str(current_path))) != self._normalized_db_path:
            raise AccessGatewayError("起動中の Access が対象 DB を開いていません。")
        return _OpenedDatabase(db=app.CurrentDb(), mode="active", app=app)

    def _open_via_dao(self) -> _OpenedDatabase:
        dao = win32com.client.Dispatch("DAO.DBEngine.120")
        db = dao.OpenDatabase(str(self.access_db_path), False, True)
        return _OpenedDatabase(db=db, mode="dao")

    def _open_via_new_access_app(self) -> _OpenedDatabase:
        app = win32com.client.Dispatch("Access.Application")
        app.Visible = False
        app.OpenCurrentDatabase(str(self.access_db_path), False)
        return _OpenedDatabase(db=app.CurrentDb(), mode="new_access", app=app)

    def _fetch_all_from_db(self, db: Any, sql: str) -> list[dict[str, Any]]:
        recordset = None
        try:
            recordset = db.OpenRecordset(sql)
            return self._recordset_to_rows(recordset)
        finally:
            if recordset is not None:
                try:
                    recordset.Close()
                except Exception:
                    pass

    def _render_sql(self, sql: str, params: Iterable[Any]) -> str:
        rendered = sql
        for value in params:
            rendered = rendered.replace("?", self._to_access_literal(value), 1)
        return rendered

    def _to_access_literal(self, value: Any) -> str:
        if value is None:
            return "Null"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, datetime):
            return f"#{value.strftime('%Y-%m-%d %H:%M:%S')}#"
        if isinstance(value, date):
            return f"#{value.strftime('%Y-%m-%d')}#"
        text = str(value).replace("'", "''")
        return f"'{text}'"

    def _recordset_to_rows(self, recordset: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        while not recordset.EOF:
            row: dict[str, Any] = {}
            for index in range(recordset.Fields.Count):
                field = recordset.Fields(index)
                value = field.Value
                if isinstance(value, pywintypes.TimeType):
                    row[field.Name] = value.Format("%Y-%m-%dT%H:%M:%S")
                else:
                    row[field.Name] = value
            rows.append(row)
            recordset.MoveNext()
        return rows

    def _normalize_path(self, path: Path) -> str:
        return str(path).replace("/", "\\").rstrip("\\").casefold()

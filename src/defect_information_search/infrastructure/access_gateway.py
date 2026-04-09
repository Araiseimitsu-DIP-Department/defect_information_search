from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pyodbc


pyodbc.pooling = True


class AccessGatewayError(RuntimeError):
    """Access ODBC 読み取りに失敗した場合の例外。"""


@dataclass
class AccessSession:
    connection: pyodbc.Connection

    def fetch_dataframe(self, sql: str, params: Iterable[Any] | None = None) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cursor.arraysize = 10000
        cursor.execute(sql, tuple(params or ()))
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
        if not rows:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame.from_records(rows, columns=columns)


@dataclass
class RowStream:
    cursor: pyodbc.Cursor
    columns: list[str]

    def __iter__(self):
        while True:
            rows = self.cursor.fetchmany(self.cursor.arraysize)
            if not rows:
                return
            for row in rows:
                yield row


class _SessionContext:
    def __init__(self, gateway: AccessGateway) -> None:  # type: ignore[name-defined]
        self._gateway = gateway
        self._connection: pyodbc.Connection | None = None

    def __enter__(self) -> AccessSession:
        self._connection = self._gateway._connect()
        return AccessSession(self._connection)

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self._connection is not None:
            self._connection.close()
            self._connection = None


class AccessGateway:
    def __init__(self, access_db_path: Path) -> None:
        self.access_db_path = access_db_path
        self._connection_string = self._build_connection_string(access_db_path)

    def session(self) -> _SessionContext:
        return _SessionContext(self)

    def fetch_dataframe(self, sql: str, params: Iterable[Any] | None = None) -> pd.DataFrame:
        with self.session() as session:
            return session.fetch_dataframe(sql, params)

    def stream_rows(self, sql: str, params: Iterable[Any] | None = None) -> _RowStreamContext:
        return _RowStreamContext(self, sql, params)

    def _connect(self) -> pyodbc.Connection:
        try:
            return pyodbc.connect(
                self._connection_string,
                autocommit=True,
                timeout=60,
            )
        except pyodbc.Error as exc:
            raise AccessGatewayError(str(exc)) from exc

    def _build_connection_string(self, access_db_path: Path) -> str:
        db_path = str(access_db_path)
        return (
            "DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            f"DBQ={db_path};"
            "ExtendedAnsiSQL=1;"
            "Exclusive=0;"
            "ReadOnly=1;"
        )


class _RowStreamContext:
    def __init__(self, gateway: AccessGateway, sql: str, params: Iterable[object] | None) -> None:
        self._gateway = gateway
        self._sql = sql
        self._params = tuple(params or ())
        self._connection: pyodbc.Connection | None = None
        self._cursor: pyodbc.Cursor | None = None

    def __enter__(self) -> RowStream:
        self._connection = self._gateway._connect()
        self._cursor = self._connection.cursor()
        self._cursor.arraysize = 10000
        self._cursor.execute(self._sql, self._params)
        columns = [column[0] for column in self._cursor.description] if self._cursor.description else []
        return RowStream(self._cursor, columns)

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None

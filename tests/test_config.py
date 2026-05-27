from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.config import AppConfig


class AppConfigTests(unittest.TestCase):
    def test_load_uses_access_backend_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            (base_dir / ".env").write_text(
                "ACCESS_DB_PATH=C:\\data\\sample.accdb\n",
                encoding="utf-8",
            )

            old_backend = os.environ.get("DATABASE_BACKEND")
            old_db_backend = os.environ.get("DB_BACKEND")
            old_path = os.environ.get("ACCESS_DB_PATH")
            try:
                os.environ.pop("DATABASE_BACKEND", None)
                os.environ.pop("DB_BACKEND", None)
                os.environ.pop("ACCESS_DB_PATH", None)
                config = AppConfig.load(base_dir)
            finally:
                if old_backend is None:
                    os.environ.pop("DATABASE_BACKEND", None)
                else:
                    os.environ["DATABASE_BACKEND"] = old_backend
                if old_db_backend is None:
                    os.environ.pop("DB_BACKEND", None)
                else:
                    os.environ["DB_BACKEND"] = old_db_backend
                if old_path is None:
                    os.environ.pop("ACCESS_DB_PATH", None)
                else:
                    os.environ["ACCESS_DB_PATH"] = old_path

        self.assertEqual(config.database_backend, "access")
        self.assertEqual(config.access_db_path, Path("C:\\data\\sample.accdb"))
        self.assertIsNone(config.postgres_dsn)

    def test_load_rejects_unknown_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            (base_dir / ".env").write_text(
                "ACCESS_DB_PATH=C:\\data\\sample.accdb\nDATABASE_BACKEND=oracle\n",
                encoding="utf-8",
            )

            old_backend = os.environ.get("DATABASE_BACKEND")
            old_db_backend = os.environ.get("DB_BACKEND")
            old_path = os.environ.get("ACCESS_DB_PATH")
            try:
                os.environ.pop("DATABASE_BACKEND", None)
                os.environ.pop("DB_BACKEND", None)
                os.environ.pop("ACCESS_DB_PATH", None)
                with self.assertRaises(ValueError):
                    AppConfig.load(base_dir)
            finally:
                if old_backend is None:
                    os.environ.pop("DATABASE_BACKEND", None)
                else:
                    os.environ["DATABASE_BACKEND"] = old_backend
                if old_db_backend is None:
                    os.environ.pop("DB_BACKEND", None)
                else:
                    os.environ["DB_BACKEND"] = old_db_backend
                if old_path is None:
                    os.environ.pop("ACCESS_DB_PATH", None)
                else:
                    os.environ["ACCESS_DB_PATH"] = old_path

    def test_load_reads_postgres_dsn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            (base_dir / ".env").write_text(
                "ACCESS_DB_PATH=C:\\data\\sample.accdb\n"
                "DB_BACKEND=postgres\n"
                "POSTGRES_CONNECTION_URL=postgresql://example\n"
                "POSTGRES_SCHEMA=public\n",
                encoding="utf-8",
            )

            old_backend = os.environ.get("DATABASE_BACKEND")
            old_db_backend = os.environ.get("DB_BACKEND")
            old_path = os.environ.get("ACCESS_DB_PATH")
            old_dsn = os.environ.get("POSTGRES_DSN")
            old_url = os.environ.get("POSTGRES_CONNECTION_URL")
            old_schema = os.environ.get("POSTGRES_SCHEMA")
            try:
                os.environ.pop("DATABASE_BACKEND", None)
                os.environ.pop("DB_BACKEND", None)
                os.environ.pop("ACCESS_DB_PATH", None)
                os.environ.pop("POSTGRES_DSN", None)
                os.environ.pop("POSTGRES_CONNECTION_URL", None)
                os.environ.pop("POSTGRES_SCHEMA", None)
                config = AppConfig.load(base_dir)
            finally:
                if old_backend is None:
                    os.environ.pop("DATABASE_BACKEND", None)
                else:
                    os.environ["DATABASE_BACKEND"] = old_backend
                if old_db_backend is None:
                    os.environ.pop("DB_BACKEND", None)
                else:
                    os.environ["DB_BACKEND"] = old_db_backend
                if old_path is None:
                    os.environ.pop("ACCESS_DB_PATH", None)
                else:
                    os.environ["ACCESS_DB_PATH"] = old_path
                if old_dsn is None:
                    os.environ.pop("POSTGRES_DSN", None)
                else:
                    os.environ["POSTGRES_DSN"] = old_dsn
                if old_url is None:
                    os.environ.pop("POSTGRES_CONNECTION_URL", None)
                else:
                    os.environ["POSTGRES_CONNECTION_URL"] = old_url
                if old_schema is None:
                    os.environ.pop("POSTGRES_SCHEMA", None)
                else:
                    os.environ["POSTGRES_SCHEMA"] = old_schema

        self.assertEqual(config.database_backend, "postgres")
        self.assertEqual(config.postgres_dsn, "postgresql://example")
        self.assertEqual(config.postgres_schema, "public")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defect_information_search.config import AppConfig
from tools.build_support import prepare
from dotenv import dotenv_values


class BuildProfileTests(unittest.TestCase):
    def test_postgres_config_does_not_require_access_path(self) -> None:
        with patch.dict(os.environ, {"DB_BACKEND": "postgres", "POSTGRES_CONNECTION_URL": "postgresql://example"}, clear=True), patch.object(AppConfig, "_candidate_env_paths", return_value=[]):
            config = AppConfig.load(ROOT)
        self.assertEqual(config.database_backend, "postgres")
        self.assertEqual(config.postgres_appearance_dsn, "postgresql://example")

    def test_access_config_still_requires_access_path(self) -> None:
        with patch.dict(os.environ, {"DB_BACKEND": "access"}, clear=True), patch.object(AppConfig, "_candidate_env_paths", return_value=[]):
            with self.assertRaisesRegex(ValueError, "ACCESS_DB_PATH"):
                AppConfig.load(ROOT)

    def test_prepare_omits_access_and_preserves_postgres_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.env"
            target = Path(temporary) / ".env"
            content = "# Access comment\nDB_BACKEND=postgres\nACCESS_DB_PATH=C:\\old.accdb\nACCESS_APPEARANCE_DB_PATH=C:\\appearance.accdb\nDATABASE_BACKEND=access\nPG_HOST=example\nPOSTGRES_CONNECTION_URL='postgresql://${PG_HOST}'\nCUSTOM=\"quote' and \\\\ slash\"\n"
            source.write_text(content, encoding="utf-8")
            prepare(source, target, "postgres")
            with patch.dict(os.environ, {}, clear=True):
                before = dotenv_values(source)
                after = dotenv_values(target)
            self.assertEqual(after["DB_BACKEND"], "postgres")
            self.assertFalse(any(key.startswith("ACCESS_") for key in after))
            self.assertNotIn("DATABASE_BACKEND", after)
            self.assertNotIn("Access comment", target.read_text(encoding="utf-8"))
            for key in ("POSTGRES_CONNECTION_URL", "CUSTOM", "PG_HOST"):
                self.assertEqual(after[key], before[key])
            self.assertEqual(source.read_text(encoding="utf-8"), content)

    def test_access_profile_preserves_settings_and_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.env"
            target = Path(temporary) / ".env"
            content = b"DB_BACKEND=access\r\nACCESS_DB_PATH=C:\\old.accdb\r\n"
            source.write_bytes(content)
            prepare(source, target, "access")
            self.assertEqual(target.read_bytes(), content)
            with self.assertRaises(ValueError):
                prepare(source, target, "postgres")
            self.assertEqual(target.read_bytes(), content)

    def test_postgres_startup_with_access_imports_blocked(self) -> None:
        # Fresh interpreter avoids modules cached by the Access SQL tests.
        code = textwrap.dedent('''
            import importlib.abc
            import sys
            from pathlib import Path
            from unittest.mock import patch, MagicMock
            sys.path.insert(0, 'src')
            class BlockAccess(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname in {'pyodbc', 'pypyodbc'} or fullname.startswith('defect_information_search.infrastructure.access'):
                        raise AssertionError('Access imported during PostgreSQL startup: ' + fullname)
            sys.meta_path.insert(0, BlockAccess())
            from defect_information_search.webview import app
            from defect_information_search.config import AppConfig
            config = AppConfig(access_db_path=Path(), database_backend='postgres', postgres_dsn='postgresql://example')
            with patch.object(AppConfig, 'load', return_value=config), patch.object(app.webview, 'create_window', return_value=MagicMock()), patch.object(app.webview, 'start') as start:
                assert app.main() == 0
                assert start.call_args.kwargs['gui'] == 'edgechromium'
            assert 'pyodbc' not in sys.modules
        ''')
        subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_postgres_exe_rejects_access_before_import_or_connection(self) -> None:
        from defect_information_search.webview import app

        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary)
            (bundle / "build_backend.txt").write_text("postgres", encoding="utf-8")
            config = AppConfig(access_db_path=Path("unused.accdb"), database_backend="access")
            with patch.object(app.sys, "frozen", True, create=True), patch.object(app, "_runtime_bundle_dir", return_value=bundle), patch.object(AppConfig, "load", return_value=config):
                with self.assertRaisesRegex(SystemExit, "PostgreSQL"):
                    app.main()


if __name__ == "__main__":
    unittest.main()

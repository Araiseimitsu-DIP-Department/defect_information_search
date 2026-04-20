from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path

import webview

from defect_information_search.config import (
    APP_NAME,
    APP_USER_MODEL_ID,
    APP_ICON_RUNTIME_FILENAME,
    AppConfig,
)
from defect_information_search.infrastructure.access.defect_repository import AccessDefectRepository
from defect_information_search.infrastructure.postgres.defect_repository import PostgresDefectRepository
from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService
from defect_information_search.webview.bridge import WebviewBridge


def _runtime_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[3]


def _runtime_config_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def _resolve_index_path(bundle_dir: Path) -> Path:
    if getattr(sys, "frozen", False):
        return bundle_dir / "defect_information_search" / "webview" / "assets" / "index.html"
    return Path(__file__).resolve().parent / "assets" / "index.html"


def _resolve_icon_path(bundle_dir: Path) -> Path | None:
    if getattr(sys, "frozen", False):
        icon_path = bundle_dir / APP_ICON_RUNTIME_FILENAME
    else:
        icon_path = Path(__file__).resolve().parents[3] / "build" / APP_ICON_RUNTIME_FILENAME
    return icon_path if icon_path.exists() else None


def main() -> int:
    bundle_dir = _runtime_bundle_dir()
    config_dir = _runtime_config_dir()
    logging.disable(logging.CRITICAL)
    _set_windows_app_user_model_id()

    try:
        config = AppConfig.load(config_dir, extra_dirs=[bundle_dir])
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

    if config.database_backend == "postgres":
        repository = PostgresDefectRepository(config.postgres_dsn)
    else:
        repository = AccessDefectRepository(config.access_db_path)

    service = DefectService(repository)
    export_service = ExportService()
    bridge = WebviewBridge(service, export_service)
    index_path = _resolve_index_path(bundle_dir)
    icon_path = _resolve_icon_path(bundle_dir)

    if not index_path.exists():
        raise FileNotFoundError(f"Frontend asset not found: {index_path}")

    window = webview.create_window(
        APP_NAME,
        url=index_path.as_uri(),
        js_api=bridge,
        width=1600,
        height=1200,
        min_size=(1200, 800),
        confirm_close=True,
        maximized=True,
        background_color="#f5f7fa",
    )
    bridge.bind_window(window)
    localization = {
        "global.quitConfirmation": "終了しますか？",
        "global.ok": "OK",
        "global.quit": "終了",
        "global.cancel": "キャンセル",
        "global.saveFile": "保存",
    }
    webview.start(
        gui="edgechromium",
        debug=False,
        localization=localization,
        icon=str(icon_path) if icon_path else None,
    )
    return 0

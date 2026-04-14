from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path

from defect_information_search.config import (
    APP_ICON_RUNTIME_FILENAME,
    APP_ICON_SOURCE_FILENAME,
    APP_NAME,
    APP_USER_MODEL_ID,
    AppConfig,
)
from defect_information_search.infrastructure.access.defect_repository import AccessDefectRepository
from defect_information_search.infrastructure.postgres.defect_repository import PostgresDefectRepository
from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService
from defect_information_search.shared.logging import configure_logging
from defect_information_search.ui.main_window import MainWindow
from defect_information_search.ui_kit.theme import APP_STYLESHEET, build_light_palette
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox


def _runtime_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def _runtime_config_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        # タスクバー表示が失敗してもアプリ本体は継続起動させる
        pass


def main() -> int:
    bundle_dir = _runtime_bundle_dir()
    config_dir = _runtime_config_dir()
    log_path = configure_logging(config_dir / "logs")
    logger = logging.getLogger(__name__)
    _set_windows_app_user_model_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # 配布版は PyInstaller が docs/window_icon.png を同梱。開発時は docs 直下の元画像を参照する。
    if getattr(sys, "frozen", False):
        icon_path = bundle_dir / "docs" / APP_ICON_RUNTIME_FILENAME
    else:
        icon_path = bundle_dir / "docs" / APP_ICON_SOURCE_FILENAME
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyle("Fusion")
    app.setPalette(build_light_palette())
    app.setStyleSheet(APP_STYLESHEET)
    try:
        config = AppConfig.load(config_dir, extra_dirs=[bundle_dir])
    except Exception as exc:
        logger.exception("Failed to load application config")
        QMessageBox.critical(None, "設定エラー", str(exc))
        return 1

    if config.database_backend == "postgres":
        repository = PostgresDefectRepository(config.postgres_dsn)
    else:
        repository = AccessDefectRepository(config.access_db_path)
    service = DefectService(repository)
    export_service = ExportService()
    window = MainWindow(service, export_service)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.showMaximized()
    logger.info("Application started. backend=%s log=%s", config.database_backend, log_path)
    return app.exec()

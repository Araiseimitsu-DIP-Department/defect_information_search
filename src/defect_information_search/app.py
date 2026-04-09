from __future__ import annotations

import sys
from pathlib import Path

from defect_information_search.config import (
    APP_ICON_RUNTIME_FILENAME,
    APP_ICON_SOURCE_FILENAME,
    APP_NAME,
    AppConfig,
)
from defect_information_search.infrastructure.access_gateway import AccessGateway
from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService
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


def main() -> int:
    bundle_dir = _runtime_bundle_dir()
    config_dir = _runtime_config_dir()
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
        QMessageBox.critical(None, "設定エラー", str(exc))
        return 1

    gateway = AccessGateway(config.access_db_path)
    service = DefectService(gateway)
    export_service = ExportService()
    window = MainWindow(service, export_service)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.showMaximized()
    return app.exec()

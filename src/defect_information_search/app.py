from __future__ import annotations

import sys
from pathlib import Path

from defect_information_search.config import APP_NAME, AppConfig
from defect_information_search.infrastructure.access_gateway import AccessGateway
from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService
from defect_information_search.ui.main_window import MainWindow
from defect_information_search.ui_kit.theme import APP_STYLESHEET, build_light_palette
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox


def main() -> int:
    root_dir = Path(__file__).resolve().parents[2]
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon_path = root_dir / "docs" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyle("Fusion")
    app.setPalette(build_light_palette())
    app.setStyleSheet(APP_STYLESHEET)
    try:
        config = AppConfig.load(root_dir)
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

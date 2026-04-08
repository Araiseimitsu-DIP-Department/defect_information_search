from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPalette


_KIT_DIR = Path(__file__).resolve().parent
_COMBO_ARROW_URL = (_KIT_DIR / "assets" / "combo_arrow_down.svg").as_posix()


def build_light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f8f9fa"))
    palette.setColor(QPalette.WindowText, QColor("#2b3437"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f1f4f6"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#2b3437"))
    palette.setColor(QPalette.Text, QColor("#2b3437"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#2b3437"))
    palette.setColor(QPalette.Highlight, QColor("#d7e2ff"))
    palette.setColor(QPalette.HighlightedText, QColor("#003d84"))
    palette.setColor(QPalette.Link, QColor("#005bbf"))
    palette.setColor(QPalette.PlaceholderText, QColor("#7d8693"))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#8d95a0"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#8d95a0"))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#8d95a0"))
    return palette


APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f8f9fa;
    color: #2b3437;
    font-family: "Yu Gothic UI", "Meiryo", sans-serif;
    font-size: 12px;
}

QFrame#Panel {
    background: #ffffff;
    border: 1px solid rgba(171, 179, 183, 0.25);
    border-radius: 14px;
}

QFrame#SoftPanel {
    background: #f1f4f6;
    border: 1px solid rgba(171, 179, 183, 0.20);
    border-radius: 14px;
}

QLabel#TitleLabel {
    font-size: 22px;
    font-weight: 800;
}

QLabel#SectionTitle {
    color: #586064;
    font-size: 11px;
    font-weight: 700;
}

QLabel#MetricValue,
QLabel#MetricDanger,
QLabel#MetricRate {
    font-size: 18px;
    font-weight: 800;
}

QLabel#MetricDanger {
    color: #b14742;
}

QLabel#FieldLabel {
    color: #586064;
    font-size: 11px;
    font-weight: 600;
}

QLabel#SummaryValue {
    color: #132033;
    font-size: 13px;
    font-weight: 700;
}

QLineEdit,
QDateEdit,
QComboBox {
    background: #f1f4f6;
    border: 1px solid rgba(171, 179, 183, 0.25);
    border-radius: 10px;
    padding: 5px 10px;
    color: #2b3437;
    selection-background-color: #d7e2ff;
    selection-color: #003d84;
    min-height: 20px;
}

QLineEdit[readOnly="true"] {
    background: #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border: none;
    background-color: rgba(0, 0, 0, 0.04);
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}

QComboBox::down-arrow {
    image: url("%s");
    width: 12px;
    height: 8px;
}

QComboBox QAbstractItemView,
QAbstractItemView {
    background-color: #ffffff;
    color: #2b3437;
    selection-background-color: #d7e2ff;
    selection-color: #003d84;
    alternate-background-color: #f1f4f6;
    border: none;
    outline: 0;
}

QPushButton {
    border: none;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 700;
}

QPushButton#PrimaryButton {
    color: #f7f7ff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005bbf, stop:1 #0050a8);
}

QPushButton#SecondaryButton {
    background: #e4e2e6;
    color: #2b3437;
}

QPushButton#DangerButton {
    background: #fde9e7;
    color: #b14742;
}

QPushButton#dialogPrimaryButton {
    color: #f7f7ff;
    border-radius: 14px;
    padding: 12px 18px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005bbf, stop:1 #0050a8);
}

QPushButton#dialogSecondaryButton,
QPushButton#calendarNavButton,
QPushButton#calendarPillButton {
    background: #eef2f7;
    color: #304255;
    border-radius: 12px;
    padding: 10px 16px;
}

QFrame#dateFieldContainer {
    background: #f1f4f6;
    border: 1px solid rgba(171, 179, 183, 0.25);
    border-radius: 10px;
    min-height: 32px;
}

QLineEdit#dateFieldDisplay {
    background: transparent;
    border: none;
    min-height: 20px;
    padding: 5px 10px;
}

QDialog#modalDialog,
QDialog#calendarDialog {
    background: transparent;
}

QFrame#modalCard,
QFrame#calendarDialogCard {
    background-color: #ffffff;
    border: 1px solid rgba(13, 77, 151, 0.08);
    border-radius: 24px;
}

QLabel#modalBadge {
    border-radius: 16px;
    padding: 0 12px;
    font-size: 11px;
    font-weight: 800;
    min-width: 72px;
}

QLabel#modalTitle,
QLabel#calendarMonthLabel {
    font-size: 18px;
    font-weight: 800;
    color: #132033;
}

QLabel#modalMessage {
    font-size: 13px;
    color: #516070;
}

QCalendarWidget#calendarWidget {
    background-color: #ffffff;
    border: none;
}

QCalendarWidget#calendarWidget QAbstractItemView:enabled {
    background-color: #ffffff;
    color: #1a1d21;
    selection-background-color: #d7e2ff;
    selection-color: #003d84;
    outline: 0;
}

QCalendarWidget#calendarWidget QTableView {
    background-color: #ffffff;
    border-radius: 16px;
    padding: 8px;
}

QCalendarWidget#calendarWidget QTableView::item {
    border-radius: 12px;
    padding: 8px;
}

QCalendarWidget#calendarWidget QTableView::item:selected {
    background-color: #005bbf;
    color: #ffffff;
}

QTableView {
    background: #ffffff;
    border: 1px solid rgba(171, 179, 183, 0.20);
    border-radius: 12px;
    gridline-color: rgba(171, 179, 183, 0.15);
    selection-background-color: #d7e2ff;
    selection-color: #003d84;
    font-size: 11px;
}

QHeaderView::section {
    background: #2b3437;
    color: #ffffff;
    border: none;
    padding: 6px;
    font-weight: 700;
}

QStatusBar {
    background: #f1f4f6;
}
""" % _COMBO_ARROW_URL

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPalette


_KIT_DIR = Path(__file__).resolve().parent
_COMBO_ARROW_URL = (_KIT_DIR / "assets" / "combo_arrow_down.svg").as_posix()


def build_light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f6f8fb"))
    palette.setColor(QPalette.WindowText, QColor("#2b3437"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f4f7fa"))
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
QMainWindow {
    background: #f6f8fb;
}

QWidget {
    color: #32404a;
    font-family: "Yu Gothic UI", "Meiryo", sans-serif;
    font-size: 12px;
}

QFrame#Panel {
    background: #ffffff;
    border: 1px solid rgba(172, 186, 198, 0.28);
    border-radius: 14px;
}

QFrame#SoftPanel {
    background: #f4f7fa;
    border: 1px solid rgba(172, 186, 198, 0.24);
    border-radius: 14px;
}

QLabel#TitleLabel {
    color: #22313d;
    font-size: 22px;
    font-weight: 800;
}

QLabel#SectionTitle {
    color: #697884;
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
    color: #506272;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}

QLabel#SummaryValue {
    color: #1f3140;
    font-size: 13px;
    font-weight: 700;
    background: transparent;
}

QLineEdit,
QDateEdit,
QComboBox {
    background: #f7f9fc;
    border: 1px solid rgba(172, 186, 198, 0.35);
    border-radius: 10px;
    padding: 4px 10px;
    color: #32404a;
    selection-background-color: #dce8f7;
    selection-color: #315b82;
    min-height: 22px;
}

QLineEdit[readOnly="true"] {
    background: #fbfcfe;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border: none;
    background-color: rgba(143, 160, 174, 0.12);
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
    color: #32404a;
    selection-background-color: #dce8f7;
    selection-color: #315b82;
    alternate-background-color: #f5f8fb;
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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4a88d9, stop:1 #3f79c7);
}

QPushButton#SecondaryButton {
    background: #e8edf2;
    color: #32404a;
}

QPushButton#DangerButton {
    background: #faece9;
    color: #c06862;
}

QPushButton#dialogPrimaryButton {
    color: #f7f7ff;
    border-radius: 14px;
    padding: 12px 18px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4a88d9, stop:1 #3f79c7);
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
    background: #f7f9fc;
    border: 1px solid rgba(172, 186, 198, 0.35);
    border-radius: 10px;
    min-height: 34px;
}

QLineEdit#dateFieldDisplay {
    background: transparent;
    border: none;
    min-height: 20px;
    padding: 2px 10px;
}

QDialog#modalDialog,
QDialog#calendarDialog {
    background: transparent;
}

QFrame#modalCard,
QFrame#calendarDialogCard {
    background-color: #ffffff;
    border: 1px solid rgba(111, 140, 168, 0.14);
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
    background: transparent;
}

QLabel#modalMessage {
    font-size: 13px;
    color: #445465;
    background: transparent;
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
    background-color: #4a88d9;
    color: #ffffff;
}

QTableView#ProductTable,
QTableView#DetailTable {
    background: #fbfdff;
    border: 1px solid rgba(172, 186, 198, 0.28);
    border-radius: 14px;
    gridline-color: transparent;
    selection-background-color: #dce8f7;
    selection-color: #315b82;
    alternate-background-color: #f5f8fb;
    font-size: 11px;
}

QTableView#ProductTable::item,
QTableView#DetailTable::item {
    padding: 6px 8px;
    border-bottom: 1px solid rgba(219, 227, 235, 0.95);
}

QHeaderView::section {
    background: #eaf0f5;
    color: #32404a;
    border: none;
    border-bottom: 1px solid rgba(190, 203, 214, 0.85);
    padding: 8px 10px;
    font-weight: 700;
}

QTableCornerButton::section {
    background: #eaf0f5;
    border: none;
    border-bottom: 1px solid rgba(190, 203, 214, 0.85);
}

QScrollBar:horizontal,
QScrollBar:vertical {
    background: transparent;
    border: none;
}

QScrollBar:horizontal {
    height: 12px;
    margin: 2px 16px 2px 16px;
}

QScrollBar:vertical {
    width: 12px;
    margin: 16px 2px 16px 2px;
}

QScrollBar::handle:horizontal,
QScrollBar::handle:vertical {
    background: #d7e2eb;
    border-radius: 6px;
    min-width: 28px;
    min-height: 28px;
}

QScrollBar::handle:horizontal:hover,
QScrollBar::handle:vertical:hover {
    background: #c7d5e1;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    border: none;
    background: transparent;
}

QStatusBar {
    background: #eef3f7;
}
""" % _COMBO_ARROW_URL

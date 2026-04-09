from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Callable

import pandas as pd
from PySide6.QtCore import QDate, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from defect_information_search.models import DEFECT_FIELDS
from defect_information_search.services.defect_service import DefectService
from defect_information_search.services.export_service import ExportService
from defect_information_search.ui.table_models import DataFrameTableModel
from defect_information_search.ui_kit.widgets.busy_indicator import run_with_busy
from defect_information_search.ui_kit.widgets.date_picker import DatePickerField
from defect_information_search.ui_kit.widgets.message_box import (
    ask_yes_no,
    show_error,
    show_info,
    show_warning,
)


class MainWindow(QMainWindow):
    TOP_PANEL_HEIGHT = 228

    def __init__(self, service: DefectService, export_service: ExportService) -> None:
        super().__init__()
        self.service = service
        self.export_service = export_service
        self.current_products = pd.DataFrame()
        self.current_all_details = pd.DataFrame()
        self.current_details = pd.DataFrame()
        self.current_part_number = ""
        self.current_date_range: tuple[date, date] | None = None

        self.setWindowTitle("品質検査課 不具合情報検索")
        self.setMinimumSize(960, 720)
        self._build_ui()
        self._init_defaults()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        root.addLayout(self._build_header())
        root.addWidget(self._build_top_area())
        root.addWidget(self._build_summary_panel())
        root.addWidget(self._build_detail_panel(), stretch=1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("準備完了")

    def _build_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("品質検査課 不具合情報検索")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch()

        close_button = QPushButton("終了")
        close_button.setObjectName("SecondaryButton")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        return layout

    def _build_top_area(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setFixedHeight(self.TOP_PANEL_HEIGHT)

        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_search_panel(), 3)
        layout.addWidget(self._build_product_panel(), 6)
        layout.addWidget(self._build_export_panel(), 3)
        return wrapper

    def _build_search_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        panel.setFixedHeight(self.TOP_PANEL_HEIGHT)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("検索条件")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.part_number_edit = QLineEdit()
        self.part_name_edit = self._readonly_line_edit()
        self.customer_edit = self._readonly_line_edit()

        date_row = QWidget()
        date_layout = QHBoxLayout(date_row)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(6)
        self.date_from_edit = DatePickerField(popup_alignment="left")
        self.date_to_edit = DatePickerField(popup_alignment="left")
        self.date_from_edit.setMinimumWidth(132)
        self.date_from_edit.setMaximumWidth(132)
        self.date_to_edit.setMinimumWidth(132)
        self.date_to_edit.setMaximumWidth(132)
        date_layout.addWidget(self.date_from_edit)
        range_label = QLabel("~")
        range_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(range_label)
        date_layout.addWidget(self._form_label("終了日"))
        date_layout.addWidget(self.date_to_edit)
        date_layout.addSpacing(4)

        self.search_button = QPushButton("検索")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self.on_search_clicked)
        self.search_button.setMinimumWidth(74)
        date_layout.addWidget(self.search_button)

        form.addRow(self._form_label("品番"), self.part_number_edit)
        form.addRow(self._form_label("品名"), self.part_name_edit)
        form.addRow(self._form_label("客先"), self.customer_edit)
        form.addRow(self._form_label("開始日"), date_row)
        layout.addLayout(form)
        return panel

    def _build_product_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        panel.setFixedHeight(self.TOP_PANEL_HEIGHT)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)

        self.product_model = DataFrameTableModel()
        self.product_table = QTableView()
        self.product_table.setObjectName("ProductTable")
        self.product_table.setModel(self.product_model)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.setShowGrid(False)
        self.product_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.product_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.verticalHeader().setDefaultSectionSize(28)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.doubleClicked.connect(self.on_product_double_clicked)
        layout.addWidget(self.product_table)
        return panel

    def _build_export_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        panel.setFixedHeight(self.TOP_PANEL_HEIGHT)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("不具合情報エクスポート")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        date_row = QWidget()
        date_row_layout = QHBoxLayout(date_row)
        date_row_layout.setContentsMargins(0, 1, 0, 1)
        date_row_layout.setSpacing(6)

        self.export_from_edit = DatePickerField(popup_alignment="right")
        self.export_to_edit = DatePickerField(popup_alignment="right")
        self.export_from_edit.setMinimumWidth(132)
        self.export_from_edit.setMaximumWidth(132)
        self.export_to_edit.setMinimumWidth(132)
        self.export_to_edit.setMaximumWidth(132)

        date_row_layout.addWidget(self._form_label("開始日"))
        date_row_layout.addWidget(self.export_from_edit)
        date_row_layout.addWidget(QLabel("~"))
        date_row_layout.addWidget(self._form_label("終了日"))
        date_row_layout.addWidget(self.export_to_edit)
        layout.addWidget(date_row)

        self.export_all_button = QPushButton("不具合情報エクスポート")
        self.export_all_button.setObjectName("SecondaryButton")
        self.export_all_button.clicked.connect(self.on_export_all_clicked)
        self._apply_action_icon(self.export_all_button, "all_export")
        layout.addWidget(self.export_all_button)

        self.export_aggregate_button = QPushButton("集計データ")
        self.export_aggregate_button.setObjectName("SecondaryButton")
        self.export_aggregate_button.clicked.connect(self.on_export_aggregate_clicked)
        self._apply_action_icon(self.export_aggregate_button, "aggregate")
        layout.addWidget(self.export_aggregate_button)

        self.export_disposal_button = QPushButton("廃棄データエクスポート")
        self.export_disposal_button.setObjectName("DangerButton")
        self.export_disposal_button.clicked.connect(self.on_export_disposal_clicked)
        self._apply_action_icon(self.export_disposal_button, "disposal")
        layout.addWidget(self.export_disposal_button)
        return panel

    def _build_summary_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("SoftPanel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        metric_row = QHBoxLayout()
        metric_row.setContentsMargins(0, 0, 0, 0)
        metric_row.setSpacing(20)
        self.quantity_value = self._add_inline_metric(metric_row, "数量", "MetricValue")
        self.defect_count_value = self._add_inline_metric(metric_row, "不具合数", "MetricDanger")
        self.defect_rate_value = self._add_inline_metric(metric_row, "不良率", "MetricRate")
        metric_row.addStretch()

        machine_label = self._form_label("号機")
        metric_row.addWidget(machine_label)

        self.machine_combo = QComboBox()
        self.machine_combo.addItem("全て")
        self.machine_combo.setMinimumWidth(110)
        self.machine_combo.currentTextChanged.connect(self.on_machine_changed)
        metric_row.addWidget(self.machine_combo)

        layout.addLayout(metric_row)

        defect_grid = QGridLayout()
        defect_grid.setContentsMargins(0, 0, 0, 0)
        defect_grid.setHorizontalSpacing(8)
        defect_grid.setVerticalSpacing(8)

        self.defect_value_labels: dict[str, QLabel] = {}
        columns_per_row = 11
        for index, (label, _) in enumerate(DEFECT_FIELDS):
            row = index // columns_per_row
            column = index % columns_per_row
            cell, value_label = self._build_defect_chip(label)
            defect_grid.addWidget(cell, row, column)
            self.defect_value_labels[label] = value_label

        layout.addLayout(defect_grid)
        return panel

    def _build_detail_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.addStretch()

        self.export_current_button = QPushButton("エクスポート")
        self.export_current_button.setObjectName("PrimaryButton")
        self.export_current_button.clicked.connect(self.on_export_current_clicked)
        self._apply_action_icon(self.export_current_button, "current_export")
        button_row.addWidget(self.export_current_button)
        layout.addLayout(button_row)

        self.detail_model = DataFrameTableModel()
        self.detail_table = QTableView()
        self.detail_table.setObjectName("DetailTable")
        self.detail_table.setModel(self.detail_model)
        self.detail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detail_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setShowGrid(False)
        self.detail_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.detail_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.verticalHeader().setDefaultSectionSize(28)
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.detail_table.horizontalHeader().setMinimumSectionSize(52)
        self.detail_table.horizontalHeader().setDefaultSectionSize(72)
        self.detail_table.setMinimumHeight(210)
        layout.addWidget(self.detail_table, stretch=1)
        return panel

    def _add_inline_metric(self, parent_layout: QHBoxLayout, label_text: str, value_object: str) -> QLabel:
        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        title = self._form_label(label_text)
        value = QLabel("0")
        value.setObjectName(value_object)

        row.addWidget(title)
        row.addWidget(value)
        parent_layout.addWidget(wrapper)
        return value

    def _build_defect_chip(self, label_text: str) -> tuple[QWidget, QLabel]:
        chip = QFrame()
        chip.setObjectName("Panel")
        chip.setMinimumHeight(34)

        row = QHBoxLayout(chip)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(6)

        label = self._form_label(label_text)
        value = QLabel("0")
        value.setObjectName("SummaryValue")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row.addWidget(label)
        row.addStretch()
        row.addWidget(value)
        return chip, value

    def _form_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _readonly_line_edit(self) -> QLineEdit:
        edit = QLineEdit()
        edit.setReadOnly(True)
        return edit

    def _apply_action_icon(self, button: QPushButton, kind: str) -> None:
        button.setIcon(self._build_action_icon(kind))
        button.setIconSize(QSize(18, 18))

    def _build_action_icon(self, kind: str) -> QIcon:
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if kind == "all_export":
            self._draw_badge(painter, QColor("#1cab4f"))
            self._draw_document_icon(painter, QColor("#ffffff"))
        elif kind == "aggregate":
            self._draw_badge(painter, QColor("#386ce8"))
            self._draw_chart_icon(painter, QColor("#ffffff"))
        elif kind == "disposal":
            self._draw_trash_icon(painter, QColor("#c06862"))
        else:
            self._draw_export_icon(painter, QColor("#ffffff"))

        painter.end()
        return QIcon(pixmap)

    def _draw_badge(self, painter: QPainter, color: QColor) -> None:
        badge_path = QPainterPath()
        badge_path.addRoundedRect(QRectF(1, 1, 18, 18), 4, 4)
        painter.fillPath(badge_path, color)

    def _draw_document_icon(self, painter: QPainter, color: QColor) -> None:
        painter.setPen(Qt.NoPen)
        page = QPainterPath()
        page.moveTo(6, 4)
        page.lineTo(12.5, 4)
        page.lineTo(15, 6.5)
        page.lineTo(15, 16)
        page.lineTo(6, 16)
        page.closeSubpath()
        painter.fillPath(page, color)

        fold = QPainterPath()
        fold.moveTo(12.5, 4)
        fold.lineTo(12.5, 6.5)
        fold.lineTo(15, 6.5)
        fold.closeSubpath()
        painter.fillPath(fold, QColor("#d9f7e4"))

        pen = QPen(QColor("#1cab4f"))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.drawLine(QPointF(7.5, 10), QPointF(13.5, 10))
        painter.drawLine(QPointF(7.5, 12.7), QPointF(13.5, 12.7))

    def _draw_chart_icon(self, painter: QPainter, color: QColor) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(5, 11, 2.6, 4), 1, 1)
        painter.drawRoundedRect(QRectF(8.8, 8, 2.6, 7), 1, 1)
        painter.drawRoundedRect(QRectF(12.6, 5, 2.6, 10), 1, 1)
        axis_pen = QPen(QColor("#dbe5ff"))
        axis_pen.setWidthF(1.1)
        painter.setPen(axis_pen)
        painter.drawLine(QPointF(4.5, 15.5), QPointF(15.8, 15.5))
        painter.drawLine(QPointF(4.5, 15.5), QPointF(4.5, 4.5))

    def _draw_trash_icon(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(QPointF(6.5, 6.5), QPointF(13.5, 6.5))
        painter.drawLine(QPointF(8.5, 4.8), QPointF(11.5, 4.8))
        painter.drawRoundedRect(QRectF(7.2, 7.2, 5.6, 7.2), 1.2, 1.2)
        painter.drawLine(QPointF(9.1, 8.8), QPointF(9.1, 13.2))
        painter.drawLine(QPointF(10, 8.8), QPointF(10, 13.2))
        painter.drawLine(QPointF(10.9, 8.8), QPointF(10.9, 13.2))

    def _draw_export_icon(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(5.2, 9.6, 9.6, 6), 1.2, 1.2)
        painter.drawLine(QPointF(10, 4.8), QPointF(10, 12))
        painter.drawLine(QPointF(7.4, 7.6), QPointF(10, 4.8))
        painter.drawLine(QPointF(12.6, 7.6), QPointF(10, 4.8))

    def _init_defaults(self) -> None:
        today = QDate.currentDate()
        three_years_ago = today.addYears(-3)
        for widget in [self.date_from_edit, self.export_from_edit]:
            widget.setDate(three_years_ago)
        for widget in [self.date_to_edit, self.export_to_edit]:
            widget.setDate(today)

    def on_search_clicked(self) -> None:
        keyword = self.part_number_edit.text().strip()
        if not keyword:
            self._show_warning("品番を入力してください。")
            return

        try:
            products = run_with_busy(
                self,
                title="品番検索",
                message="品番候補を取得しています。",
                task=lambda: self.service.find_products(keyword),
            )
        except Exception as exc:
            self._show_error(str(exc))
            return

        self.current_products = products
        self.product_model.set_dataframe(products)
        self._resize_tables()

        if products.empty:
            self._clear_result_views(clear_product_fields=True)
            self._show_info("該当する品番はありません。")
            return

        if len(products.index) == 1:
            self._set_product_fields_from_row(0)
            self._load_part_data(self._product_value(0, 0))
            return

        self.part_name_edit.clear()
        self.customer_edit.clear()
        self._clear_result_views(clear_product_fields=False)
        self.statusBar().showMessage("候補から品番を選択してください。")

    def on_product_double_clicked(self) -> None:
        index = self.product_table.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        self._set_product_fields_from_row(row)
        self._load_part_data(self._product_value(row, 0))

    def on_machine_changed(self, text: str) -> None:
        part_number = self.part_number_edit.text().strip()
        if not part_number:
            return
        machine = None if self.machine_combo.currentIndex() == 0 else text
        if self._has_cached_details(part_number):
            self._apply_cached_result(machine)
            return
        self._load_part_data(part_number, machine)

    def on_export_current_clicked(self) -> None:
        if self.current_details.empty:
            self._show_warning("出力できるデータがありません。")
            return
        if not ask_yes_no(self, "検索結果エクスポート", "表示中の一覧を Excel に出力しますか。"):
            return

        path = self._select_save_path(self._current_export_filename())
        if not path:
            return

        try:
            run_with_busy(
                self,
                title="検索結果エクスポート",
                message="Excel ファイルを作成しています。",
                task=lambda: self.export_service.export_dataframe(self.current_details, path),
            )
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._show_info(f"Excel ファイルを保存しました。\n{path}")

    def on_export_all_clicked(self) -> None:
        start_date, end_date = self._export_dates()
        if start_date > end_date:
            self._show_warning("開始日と終了日の指定が正しくありません。")
            return
        if not ask_yes_no(self, "不具合情報エクスポート", "Excel に出力しますか。"):
            return

        path = self._select_save_path("不具合情報一覧.xlsx")
        if not path:
            return

        def task() -> None:
            exported = self.service.export_all_defects_to_excel(
                self.export_service,
                path,
                start_date,
                end_date,
            )
            if exported == 0:
                raise ValueError("対象期間のデータがありません。")

        try:
            run_with_busy(
                self,
                title="不具合情報エクスポート",
                message="Excel ファイルを作成しています。",
                task=task,
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._show_info(f"Excel ファイルを保存しました。\n{path}")

    def on_export_aggregate_clicked(self) -> None:
        filename = (
            f"{self.export_from_edit.date().toString('yyMMdd')}"
            f"~{self.export_to_edit.date().toString('yyMMdd')}集計データ.xlsx"
        )
        self._export_range(
            title="集計データエクスポート",
            default_name=filename,
            loader=self.service.export_aggregate,
            formatter="aggregate",
        )

    def on_export_disposal_clicked(self) -> None:
        self._export_range(
            title="廃棄データエクスポート",
            default_name="廃棄データ.xlsx",
            loader=self.service.export_disposal,
            formatter="disposal",
        )

    def _export_range(
        self,
        *,
        title: str,
        default_name: str,
        loader: Callable[[date, date], pd.DataFrame],
        formatter: str | None = None,
    ) -> None:
        start_date, end_date = self._export_dates()
        if start_date > end_date:
            self._show_warning("開始日と終了日の指定が正しくありません。")
            return
        if not ask_yes_no(self, title, "Excel に出力しますか。"):
            return

        path = self._select_save_path(default_name)
        if not path:
            return

        def task() -> None:
            dataframe = loader(start_date, end_date)
            if dataframe.empty:
                raise ValueError("対象期間のデータがありません。")
            self.export_service.export_dataframe(dataframe, path, formatter=formatter)

        try:
            run_with_busy(
                self,
                title=title,
                message="Excel ファイルを作成しています。",
                task=task,
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._show_info(f"Excel ファイルを保存しました。\n{path}")

    def _load_part_data(self, part_number: str, machine: str | None = None) -> None:
        start_date, end_date = self._search_dates()
        if start_date > end_date:
            self._show_warning("開始日と終了日の指定が正しくありません。")
            return

        if self._has_cached_details(part_number, start_date, end_date):
            self._apply_cached_result(machine)
            return

        try:
            result = run_with_busy(
                self,
                title="不具合情報検索",
                message="不具合情報を集計しています。",
                task=lambda: self.service.load_search_result(part_number, start_date, end_date, None),
            )
        except Exception as exc:
            self._show_error(str(exc))
            return

        if not result.summary:
            self._clear_result_views(clear_product_fields=False)
            self._show_info("指定条件の実績はありません。")
            return

        self.current_part_number = part_number
        self.current_date_range = (start_date, end_date)
        self.current_all_details = result.all_details.copy()
        self._refresh_machine_combo(result.machines, machine)
        self._apply_cached_result(machine)

    def _apply_summary(self, summary: dict[str, object]) -> None:
        self.quantity_value.setText(self._format_integer(summary.get("quantity"), zero_text="0"))
        self.defect_count_value.setText(self._format_integer(summary.get("defect_count"), zero_text="0"))

        rate = summary.get("defect_rate")
        if rate in {None, ""}:
            self.defect_rate_value.setText("0.00%")
        else:
            self.defect_rate_value.setText(f"{float(rate) * 100:.2f}%")

        for label, widget in self.defect_value_labels.items():
            widget.setText(self._format_integer(summary.get(label), zero_text="0"))

    def _clear_result_views(self, *, clear_product_fields: bool) -> None:
        if clear_product_fields:
            self.part_name_edit.clear()
            self.customer_edit.clear()

        self.current_part_number = ""
        self.current_date_range = None
        self.current_all_details = pd.DataFrame()
        self.current_details = pd.DataFrame()
        self.detail_model.set_dataframe(self.current_details)
        self.quantity_value.setText("0")
        self.defect_count_value.setText("0")
        self.defect_rate_value.setText("0.00%")

        for widget in self.defect_value_labels.values():
            widget.setText("0")

        self.machine_combo.blockSignals(True)
        self.machine_combo.clear()
        self.machine_combo.addItem("全て")
        self.machine_combo.blockSignals(False)

    def _has_cached_details(
        self,
        part_number: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> bool:
        if self.current_all_details.empty:
            return False
        if self.current_part_number != part_number:
            return False
        if start_date is None or end_date is None:
            return self.current_date_range is not None
        return self.current_date_range == (start_date, end_date)

    def _apply_cached_result(self, machine: str | None) -> None:
        result = self.service.build_search_result(self.current_all_details, machine)
        self._refresh_machine_combo(result.machines, machine)
        self._apply_summary(result.summary)
        self.current_details = result.details
        self.detail_model.set_dataframe(result.details)
        self._resize_tables()
        self.statusBar().showMessage("検索結果を表示しました。")

    def _refresh_machine_combo(self, machines: list[str], machine: str | None) -> None:
        self.machine_combo.blockSignals(True)
        self.machine_combo.clear()
        self.machine_combo.addItems(machines)
        selected_machine = machine if machine is not None else machines[0]
        combo_index = self.machine_combo.findText(selected_machine)
        self.machine_combo.setCurrentIndex(combo_index if combo_index >= 0 else 0)
        self.machine_combo.blockSignals(False)

    def _set_product_fields_from_row(self, row: int) -> None:
        self.part_number_edit.setText(self._product_value(row, 0))
        self.part_name_edit.setText(self._product_value(row, 1))
        self.customer_edit.setText(self._product_value(row, 2))

    def _product_value(self, row: int, column: int) -> str:
        value = self.current_products.iat[row, column]
        return "" if value is None else str(value)

    def _resize_tables(self) -> None:
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._apply_detail_column_widths()

    def _apply_detail_column_widths(self) -> None:
        widths = {
            0: 60,
            1: 104,
            2: 100,
            3: 86,
            4: 56,
            5: 92,
            6: 92,
            7: 92,
            8: 92,
            9: 92,
            10: 56,
            11: 72,
            12: 88,
            13: 68,
        }
        for column, width in widths.items():
            if column < self.detail_model.columnCount():
                self.detail_table.setColumnWidth(column, width)

    def _search_dates(self) -> tuple[date, date]:
        return self._qdate_to_date(self.date_from_edit.date()), self._qdate_to_date(self.date_to_edit.date())

    def _export_dates(self) -> tuple[date, date]:
        return self._qdate_to_date(self.export_from_edit.date()), self._qdate_to_date(self.export_to_edit.date())

    def _qdate_to_date(self, qdate: QDate) -> date:
        return datetime(qdate.year(), qdate.month(), qdate.day()).date()

    def _format_integer(self, value: object, *, zero_text: str = "") -> str:
        if value in {None, ""}:
            return zero_text
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return str(value)

    def _select_save_path(self, default_name: str) -> Path | None:
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "保存先を選択",
            str(Path.home() / "Desktop" / default_name),
            "Excel Files (*.xlsx)",
        )
        return Path(selected) if selected else None

    def _current_export_filename(self) -> str:
        part_number = self.current_part_number.strip() or self.part_number_edit.text().strip()
        if not part_number:
            return "品質検査課_不具合情報.xlsx"
        safe_part_number = "".join(
            character for character in part_number if character not in '<>:"/\\|?*'
        ).strip()
        if not safe_part_number:
            return "品質検査課_不具合情報.xlsx"
        return f"{safe_part_number}_不具合情報.xlsx"

    def _show_warning(self, message: str) -> None:
        show_warning(self, "確認", message)

    def _show_info(self, message: str) -> None:
        show_info(self, "確認", message)

    def _show_error(self, message: str) -> None:
        show_error(self, "エラー", message)

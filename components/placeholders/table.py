from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView)
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import Qt, pyqtSignal

from helper import FontDelegate

class PlaceholderTable(QTableWidget):
    """
    A reusable widget for displaying a grid of placeholders_list.

    This table automatically arranges a list of placeholder strings into a
    grid. It is configured to be read-only, with a compact appearance suitable
    for displaying helper text. It emits a signal when a placeholder is
    double-clicked, allowing parent widgets to handle the insertion logic.
    """
    placeholder_double_clicked = pyqtSignal(str)

    def __init__(self, placeholders_list: list[str], num_columns: int, parent=None):
        """
        Initializes the PlaceholderTable.

        Args:
            placeholders_list (list[str]): The list of placeholder strings to display.
            num_columns (int): The number of columns for the grid layout.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._placeholders_list = placeholders_list
        self._num_columns = num_columns
        self._setup_ui()
        self._populate_table()
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _setup_ui(self):
        """Configures the appearance and behavior of the table."""
        num_rows = (len(self._placeholders_list) + self._num_columns - 1) // self._num_columns
        self.setRowCount(num_rows)
        self.setColumnCount(self._num_columns)

        self.setItemDelegate(FontDelegate(font_family="Consolas", font_size=9))
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setShowGrid(False)

    def _populate_table(self):
        """Fills the table with placeholder items."""
        for i, placeholder in enumerate(self._placeholders_list):
            row, col = divmod(i, self._num_columns)
            item = QTableWidgetItem(placeholder)
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(f"Double-click to insert {placeholder}")
            self.setItem(row, col, item)

    def _on_cell_double_clicked(self, row: int, column: int):
        """Handles the double-click event and emits the placeholder text."""
        item = self.item(row, column)
        if item:
            self.placeholder_double_clicked.emit(item.text())

    def set_compact_height(self):
        """
        Adjusts the table's height to be as compact as possible, fitting
        its content without extra space. This is useful when the table is
        part of a larger layout.
        """
        # self.resizeRowsToContents() often includes default padding which can be too large.
        # We manually calculate the row height based on font metrics for a tighter fit.
        font = QFont("Consolas", 9)
        metrics = QFontMetrics(font)
        # Add a small vertical padding (e.g., 4 pixels)
        row_height = metrics.height() #+ 2

        total_height = self.horizontalHeader().height()
        for i in range(self.rowCount()):
            self.setRowHeight(i, row_height)
            total_height += row_height
        # Add a small buffer for borders/padding
        total_height += self.frameWidth() * 2
        self.setFixedHeight(total_height)

    def set_disabled_placeholders(self, disabled_list: list[str]):
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and item.text():
                    if item.text() in disabled_list:
                        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    else:
                        item.setFlags(item.flags() | Qt.ItemIsEnabled)
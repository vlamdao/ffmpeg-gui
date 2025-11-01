
import json, os
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QFormLayout, QLabel,
    QMessageBox, QMenu, QDialog, QTextEdit,
    QLineEdit, QHeaderView,  QDialogButtonBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from helper import FontDelegate

# Import constants directly for consistency
from helper.placeholders import GENERAL_PLACEHOLDERS

class PresetDialog(QDialog):
    """A dialog for adding or editing a preset (name and command)."""
    _INPUT_WIDTH = 500
    _CMD_INPUT_HEIGHT = 70

    def __init__(self, parent=None, title="Preset", preset_name="", preset_command=""):
        """Initializes the PresetDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            title (str, optional): The window title for the dialog. Defaults to "Preset".
            preset_name (str, optional): The initial text for the preset name field. Defaults to "".
            preset_command (str, optional): The initial text for the command field. Defaults to "".
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self._preset_name = preset_name
        self._preset_command = preset_command
        self._setup_ui()

    def _setup_ui(self):
        """Initializes and arranges all UI components."""
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Creates all the widgets needed for the dialog."""
        self._name_input = QLineEdit(self._preset_name)
        self._name_input.setMinimumWidth(self._INPUT_WIDTH)

        self._placeholder_table = self._create_placeholder_table()
        self._placeholder_table.setMinimumWidth(self._INPUT_WIDTH)
        self._placeholder_table.setMaximumHeight(65) # Limit height for 2 rows

        self._cmd_input = QTextEdit(self._preset_command)
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumWidth(self._INPUT_WIDTH)
        self._cmd_input.setMinimumHeight(self._CMD_INPUT_HEIGHT)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def _setup_layout(self):
        """Configures the layout and adds widgets to it."""
        layout = QFormLayout(self)
        layout.addRow("Preset Name:", self._name_input)
        layout.addRow("Placeholders:", self._placeholder_table)
        layout.addRow("Command:", self._cmd_input)
        layout.addWidget(self._button_box)

    def _create_placeholder_table(self):
        """Creates and populates the placeholder table widget."""
        placeholders = GENERAL_PLACEHOLDERS
        
        num_columns = 3
        # Calculate the number of rows needed dynamically to avoid magic numbers
        num_rows = (len(placeholders) + num_columns - 1) // num_columns

        table = QTableWidget()
        table.setColumnCount(num_columns)
        table.setItemDelegate(FontDelegate(font_family="Consolas", font_size=9))
        table.setRowCount(num_rows)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setShowGrid(False)

        for i, placeholder in enumerate(placeholders):
            row = i // num_columns
            col = i % num_columns
            item = QTableWidgetItem(placeholder)
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(f"Double-click to insert {placeholder}")
            table.setItem(row, col, item)

        table.cellDoubleClicked.connect(self._on_placeholder_double_clicked)
        return table

    def _on_placeholder_double_clicked(self, row, column):
        """Inserts the placeholder text into the command input at the cursor position."""
        item = self._placeholder_table.item(row, column)
        if item:
            self._cmd_input.insertPlainText(item.text())

    def get_preset(self):
        """Returns the preset name and command from the input fields."""
        return self._name_input.text().strip(), self._cmd_input.toPlainText().strip()

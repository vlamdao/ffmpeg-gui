
import json, os
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QFormLayout, QLabel,
    QMessageBox, QMenu, QDialog, QTextEdit,
    QLineEdit, QHeaderView,  QDialogButtonBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from helper import FontDelegate

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
        
        # =======================================
        # Create widgets
        # =======================================
        self.name_input = QLineEdit(preset_name)
        self.placeholder_table = self._create_placeholder_table()
        self.cmd_input = QTextEdit(preset_command)
        self.cmd_input.setFont(QFont("Consolas", 9))
        
        # Set initial sizes (can be adjusted by user)
        self.name_input.setMinimumWidth(self._INPUT_WIDTH)
        self.placeholder_table.setMinimumWidth(self._INPUT_WIDTH)
        self.placeholder_table.setMaximumHeight(65) # Limit height for 2 rows
        self.cmd_input.setMinimumWidth(self._INPUT_WIDTH)
        self.cmd_input.setMinimumHeight(self._CMD_INPUT_HEIGHT)

        # =======================================
        # Create layout and add widgets
        # =======================================
        layout = QFormLayout(self)
        layout.addRow("Preset Name:", self.name_input)
        layout.addRow("Placeholders:", self.placeholder_table)
        layout.addRow("Command:", self.cmd_input)

        # =======================================
        # Add standard buttons
        # =======================================
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _create_placeholder_table(self):
        """Creates and populates the placeholder table widget."""
        table = QTableWidget()
        table.setFont(QFont("Consolas", 9))
        table.setColumnCount(3)
        table.setRowCount(2)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        # Stretch columns to fill the available width
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        placeholders = [
            "{inputfile_folder}", "{inputfile_name}", "{inputfile_ext}",
            "{output_folder}", "{outputfile_name}", "{concatfile_path}",
        ]

        for i, placeholder in enumerate(placeholders):
            if not placeholder: continue
            row = i // 3
            col = i % 3
            item = QTableWidgetItem(placeholder)
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(f"Double-click to insert {placeholder}")
            table.setItem(row, col, item)

        table.cellDoubleClicked.connect(self._on_placeholder_double_clicked)
        return table

    def _on_placeholder_double_clicked(self, row, column):
        """Inserts the placeholder text into the command input at the cursor position."""
        item = self.placeholder_table.item(row, column)
        if item:
            self.cmd_input.insertPlainText(item.text())

    def get_preset(self):
        """Returns the preset name and command from the input fields."""
        return self.name_input.text().strip(), self.cmd_input.toPlainText().strip()

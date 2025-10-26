
import json, os
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QFormLayout,
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
        self.cmd_input = QTextEdit(preset_command)
        self.cmd_input.setFont(QFont("Consolas", 9))
        
        # Set initial sizes (can be adjusted by user)
        self.name_input.setMinimumWidth(self._INPUT_WIDTH)
        self.cmd_input.setMinimumWidth(self._INPUT_WIDTH)
        self.cmd_input.setMinimumHeight(self._CMD_INPUT_HEIGHT)

        # =======================================
        # Create layout and add widgets
        # =======================================
        layout = QFormLayout(self)
        layout.addRow("Preset Name:", self.name_input)
        layout.addRow("Command:", self.cmd_input)

        # =======================================
        # Add standard buttons
        # =======================================
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_preset(self):
        """Returns the preset name and command from the input fields."""
        return self.name_input.text().strip(), self.cmd_input.toPlainText().strip()

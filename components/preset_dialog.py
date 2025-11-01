
import json, os
from PyQt5.QtWidgets import (
    QFormLayout, QDialog, QTextEdit,
    QLineEdit, QDialogButtonBox
)
from PyQt5.QtGui import QFont
from .placeholder_table import PlaceholderTable

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

        self._placeholder_table = PlaceholderTable(
            placeholders=GENERAL_PLACEHOLDERS,
            num_columns=3,
            parent=self
        )
        self._placeholder_table.setMinimumWidth(self._INPUT_WIDTH)
        self._placeholder_table.set_compact_height()

        self._cmd_input = QTextEdit(self._preset_command)
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumWidth(self._INPUT_WIDTH)
        self._cmd_input.setMinimumHeight(self._CMD_INPUT_HEIGHT)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        
        self._placeholder_table.placeholder_double_clicked.connect(self._cmd_input.insertPlainText)

    def _setup_layout(self):
        """Configures the layout and adds widgets to it."""
        layout = QFormLayout(self)
        layout.addRow("Preset Name:", self._name_input)
        layout.addRow("Placeholders:", self._placeholder_table)
        layout.addRow("Command:", self._cmd_input)
        layout.addWidget(self._button_box)

    def get_preset(self):
        """Returns the preset name and command from the input fields."""
        return self._name_input.text().strip(), self._cmd_input.toPlainText().strip()

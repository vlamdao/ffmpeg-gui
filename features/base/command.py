from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont
from typing import TYPE_CHECKING

class BaseCommandTemplate(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cmd_input: QTextEdit
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._cmd_input = QTextEdit()
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumHeight(80)

        layout.addWidget(self._cmd_input)

    def get_command_template(self) -> list[str]:
        """
        Returns the command(s) from the input widget as a list of strings.
        Each line is treated as a separate command.
        """
        return [line.strip() for line in self._cmd_input.toPlainText().splitlines() if line.strip()]
    
    def generate_commands(self, *args, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
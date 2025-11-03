from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components import Placeholders

class BaseCommandTemplate(QWidget):

    def __init__(self, placeholders: 'Placeholders', parent=None):
        super().__init__(parent)
        self._cmd_input: QTextEdit
        self._placeholders = placeholders
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        QVBoxLayout.setContentsMargins(0, 0, 0, 0)

        self._cmd_input = QTextEdit()
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumHeight(80)

        layout.addWidget(self._cmd_input)

    def get_command_template(self) -> str:
        return self._cmd_input.toPlainText().strip()
    
    def generate_command(self, *args, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
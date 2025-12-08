from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont
from typing import TYPE_CHECKING

class BaseCommandTemplate(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cmd_input: QTextEdit
        self._DEFAULT_CMD = []

        self._setup_ui()
        self._set_default_cmd()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._cmd_input = QTextEdit()
        self._cmd_input.setFont(QFont("Consolas", 9))
        # self._cmd_input.setMinimumHeight(80)
        self._cmd_input.setFixedHeight(90)

        layout.addWidget(self._cmd_input)

    def _set_default_cmd(self):
        if not self._DEFAULT_CMD:
            return
        self._set_command(self._DEFAULT_CMD)
    
    def _set_command(self, command: str | list[str]):
        if isinstance(command, str):
            self._cmd_input.setText(command)
        else:
            self._cmd_input.setText("\n\n".join(command))       

    def insert_placeholder(self, placeholder: str):
        self._cmd_input.insertPlainText(placeholder)

    def get_command_template(self) -> list[str]:
        """
        Returns the command(s) from the input widget as a list of strings.
        Each line is treated as a separate command.
        """
        return [line.strip() for line in self._cmd_input.toPlainText().splitlines() if line.strip()]
    
    def generate_commands(self, *args, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
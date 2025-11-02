from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont

from .placeholders import VideoCutterPlaceholders
from components import PlaceholderTable


class CommandTemplate(QWidget):

    def __init__(self, input_file: str, output_folder: str, parent=None):
        super().__init__(parent)
        self._placeholders = VideoCutterPlaceholders()
        self._placeholder_table: PlaceholderTable
        self._command_template: QTextEdit
        self._input_file = input_file
        self._output_folder = output_folder
        
        self._DEFAULT_COMMAND_TEMPLATE = (
            f'ffmpeg -y -loglevel warning -i "{self._placeholders.get_INPUTFILE_FOLDER()}/{self._placeholders.get_INPUTFILE_NAME()}.{self._placeholders.get_INPUTFILE_EXT()}" '
            f'-ss {self._placeholders.get_START_TIME()} -to {self._placeholders.get_END_TIME()} '
            f'-c copy "{self._placeholders.get_OUTPUT_FOLDER()}/{self._placeholders.get_INPUTFILE_NAME()}--{self._placeholders.get_SAFE_START_TIME()}--'
            f'{self._placeholders.get_SAFE_END_TIME()}.{self._placeholders.get_INPUTFILE_EXT()}"'
        )

        self._setup_ui()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        self._placeholder_table = PlaceholderTable(
            placeholders_list=self._placeholders.get_placeholders_list(),
            num_columns=5,
            parent=self
        )
        self._placeholder_table.set_compact_height()

        self._command_template = QTextEdit()
        self._command_template.setText(self._DEFAULT_COMMAND_TEMPLATE)
        self._command_template.setFixedHeight(90)
        self._command_template.setFont(QFont("Consolas", 9))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._placeholder_table)
        layout.addWidget(self._command_template)
        self._placeholder_table.placeholder_double_clicked.connect(self._command_template.insertPlainText)

    def get_command_template(self) -> str:
        """Returns the command template from the text edit."""
        return self._command_template.toPlainText().strip()

    def generate_command(self, start_ms: int, end_ms: int) -> str | None:
        """Creates a fully rendered FFmpeg command for a given time segment."""
        template = self.get_command_template()
        if not template:
            return None

        replacements = self._placeholders.get_replacements(self._input_file, self._output_folder, start_ms, end_ms)
        complete_command = self._placeholders.replace_placeholders(template, replacements)
        return complete_command

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from dataclasses import dataclass

from helper import ms_to_time_str
from helper.placeholders import (
    PLACEHOLDER_INPUTFILE_FOLDER, PLACEHOLDER_INPUTFILE_NAME, PLACEHOLDER_INPUTFILE_EXT,
    PLACEHOLDER_START_TIME, PLACEHOLDER_END_TIME, PLACEHOLDER_OUTPUT_FOLDER,
    PLACEHOLDER_SAFE_START_TIME, PLACEHOLDER_SAFE_END_TIME,
    VIDEO_CUTTER_PLACEHOLDERS
)

@dataclass
class CommandContext:
    """A data class to hold all the values needed to generate a command."""
    inputfile_folder: str
    inputfile_name: str
    inputfile_ext: str
    start_time: str
    end_time: str
    output_folder: str
    safe_start_time: str
    safe_end_time: str

class CommandTemplate(QWidget):
    
    DEFAULT_COMMAND_TEMPLATE = (
        f'ffmpeg -y -loglevel warning -i "{PLACEHOLDER_INPUTFILE_FOLDER}/{PLACEHOLDER_INPUTFILE_NAME}.{PLACEHOLDER_INPUTFILE_EXT}" '
        f'-ss {PLACEHOLDER_START_TIME} -to {PLACEHOLDER_END_TIME} '
        f'-c copy "{PLACEHOLDER_OUTPUT_FOLDER}/{PLACEHOLDER_INPUTFILE_NAME}--{PLACEHOLDER_SAFE_START_TIME}--'
        f'{PLACEHOLDER_SAFE_END_TIME}.{PLACEHOLDER_INPUTFILE_EXT}"'
    )

    def __init__(self, video_path: str, output_path: str, parent=None):
        super().__init__(parent)
        self._placeholder_table: QTableWidget
        self._command_template: QTextEdit
        self._video_path = video_path
        self._output_path = output_path
        self._setup_ui()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        self._placeholder_table = self._create_placeholder_table()
        self._command_template = QTextEdit()
        self._command_template.setText(self.DEFAULT_COMMAND_TEMPLATE)
        self._command_template.setFixedHeight(90)
        self._command_template.setFont(QFont("Consolas", 9))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._placeholder_table)
        layout.addWidget(self._command_template)

    def _create_placeholder_table(self) -> QTableWidget:
        """Creates and populates the placeholder table widget."""
        num_columns = 5
        num_rows = (len(VIDEO_CUTTER_PLACEHOLDERS) + num_columns - 1) // num_columns
        table = QTableWidget()
        table.setColumnCount(num_columns)
        table.setRowCount(num_rows)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setShowGrid(False)
        for i, placeholder in enumerate(VIDEO_CUTTER_PLACEHOLDERS):
            row = i // num_columns
            col = i % num_columns
            item = QTableWidgetItem(placeholder)
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(f"Double-click to insert {placeholder}")
            item.setFont(QFont("Consolas", 9))
            table.setItem(row, col, item)

        # Explicitly calculate and set the fixed height for the table
        # to ensure it's perfectly compact.
        table.resizeRowsToContents()
        total_height = 0
        for i in range(table.rowCount()):
            total_height += table.rowHeight(i)
        total_height += table.frameWidth() * 2
        table.setFixedHeight(total_height)

        table.cellDoubleClicked.connect(self._on_placeholder_double_clicked)
        return table

    def _on_placeholder_double_clicked(self, row: int, column: int):
        """
        Inserts the placeholder text into the command input at the cursor position.
        """
        item = self._placeholder_table.item(row, column)
        if item:
            self._command_template.insertPlainText(item.text())

    def _replace_placeholders(self, context: CommandContext) -> str:
        template = self.get_command_template()

        replacements = {
            PLACEHOLDER_INPUTFILE_FOLDER: context.inputfile_folder,
            PLACEHOLDER_INPUTFILE_NAME: context.inputfile_name,
            PLACEHOLDER_INPUTFILE_EXT: context.inputfile_ext,
            PLACEHOLDER_START_TIME: context.start_time,
            PLACEHOLDER_END_TIME: context.end_time,
            PLACEHOLDER_OUTPUT_FOLDER: context.output_folder,
            PLACEHOLDER_SAFE_START_TIME: context.safe_start_time,
            PLACEHOLDER_SAFE_END_TIME: context.safe_end_time,
        }
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
            
        return template

    def get_command_template(self) -> str:
        """Returns the command template from the text edit."""
        return self._command_template.toPlainText().strip()

    def generate_command(self, start_ms: int, end_ms: int) -> str | None:
        """Creates a fully rendered FFmpeg command for a given time segment."""
        template = self.get_command_template()
        if not template:
            return None

        start_str = ms_to_time_str(start_ms)
        end_str = ms_to_time_str(end_ms)
        safe_start_str = start_str.replace(":", "-").replace(".", "_")
        safe_end_str = end_str.replace(":", "-").replace(".", "_")

        inputfile_name, inputfile_ext = os.path.splitext(os.path.basename(self._video_path))

        context = CommandContext(
            inputfile_folder=os.path.dirname(self._video_path),
            inputfile_name=inputfile_name,
            inputfile_ext=inputfile_ext.lstrip('.'),
            start_time=start_str,
            end_time=end_str,
            output_folder=self._output_path,
            safe_start_time=safe_start_str,
            safe_end_time=safe_end_str
        )
        complete_command = self._replace_placeholders(context)
        return complete_command

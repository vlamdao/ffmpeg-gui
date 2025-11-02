import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont

from helper import ms_to_time_str
from components import PlaceholderTable, PlaceholderManager
from helper.placeholders import (
    PLACEHOLDER_START_TIME, PLACEHOLDER_END_TIME, PLACEHOLDER_OUTPUT_FOLDER,
    PLACEHOLDER_SAFE_START_TIME, PLACEHOLDER_SAFE_END_TIME,
    VIDEO_CUTTER_PLACEHOLDERS
)

class VideoCutterPlaceholderManager(PlaceholderManager):
    """Mở rộng PlaceholderManager cho các placeholder của Video Cutter."""
    def get_replacements(self, video_path: str, start_ms: int, end_ms: int) -> dict[str, str]:
        """
        Tạo ra các giá trị thay thế cho tất cả các placeholder của video cutter.
        """
        # Tạo một tuple file đầu vào giả để tái sử dụng logic của lớp cha
        input_file_tuple = (0, os.path.basename(video_path), os.path.dirname(video_path))
        replacements = self.get_general_replacements(input_file_tuple)

        start_str = ms_to_time_str(start_ms)
        end_str = ms_to_time_str(end_ms)
        safe_start_str = start_str.replace(":", "-").replace(".", "_")
        safe_end_str = end_str.replace(":", "-").replace(".", "_")

        # Thêm các placeholder cụ thể của video cutter
        cutter_replacements = {
            PLACEHOLDER_START_TIME: start_str,
            PLACEHOLDER_END_TIME: end_str,
            PLACEHOLDER_SAFE_START_TIME: safe_start_str,
            PLACEHOLDER_SAFE_END_TIME: safe_end_str,
        }
        
        replacements.update(cutter_replacements)
        return replacements

class CommandTemplate(QWidget):
    
    DEFAULT_COMMAND_TEMPLATE = (
        f'ffmpeg -y -loglevel warning -i "{PLACEHOLDER_INPUTFILE_FOLDER}/{PLACEHOLDER_INPUTFILE_NAME}.{PLACEHOLDER_INPUTFILE_EXT}" '
        f'-ss {PLACEHOLDER_START_TIME} -to {PLACEHOLDER_END_TIME} '
        f'-c copy "{PLACEHOLDER_OUTPUT_FOLDER}/{PLACEHOLDER_INPUTFILE_NAME}--{PLACEHOLDER_SAFE_START_TIME}--'
        f'{PLACEHOLDER_SAFE_END_TIME}.{PLACEHOLDER_INPUTFILE_EXT}"'
    )

    def __init__(self, video_path: str, output_path: str, parent=None):
        super().__init__(parent)
        self._placeholder_table: PlaceholderTable
        self._command_template: QTextEdit
        self._video_path = video_path
        self._output_path = output_path
        
        # Giả lập đối tượng OutputPath để truyền vào PlaceholderManager
        class TempOutputPath:
            def get_completed_output_path(self, _): return output_path
        self._placeholder_manager = VideoCutterPlaceholderManager(TempOutputPath())

        self._setup_ui()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        self._placeholder_table = PlaceholderTable(
            placeholders=VIDEO_CUTTER_PLACEHOLDERS,
            num_columns=5,
            parent=self
        )
        self._placeholder_table.set_compact_height()

        self._command_template = QTextEdit()
        self._command_template.setText(self.DEFAULT_COMMAND_TEMPLATE)
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

        replacements = self._placeholder_manager.get_replacements(self._video_path, start_ms, end_ms)
        complete_command = self._placeholder_manager.replace(template, replacements)
        return complete_command

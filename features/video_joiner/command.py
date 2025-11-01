from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QTextEdit)
from PyQt5.QtGui import QFont

from components import PlaceholderTable
from helper.placeholders import VIDEO_JOINER_PLACEHOLDERS

class CommandTemplate(QWidget):
    """
    A widget for managing the command template for video joining.
    It includes placeholders and a text input for the FFmpeg command.
    """
    # Default command templates for each join method
    CONCAT_DEMUXER_CMD = 'ffmpeg -y -f concat -safe 0 -i "{concatfile_path}" -c copy "{output_folder}/joined_video.mp4"'
    CONCAT_FILTER_CMD = 'ffmpeg -y {inputs} -filter_complex "{filter_script}" -map "[v]" -map "[a]" "{output_folder}/joined_video_re-encoded.mp4"'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._placeholder_table: PlaceholderTable
        self._cmd_input: QTextEdit
        self._setup_ui()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # --- Placeholders ---
        placeholder_group = QGroupBox("Placeholders")
        placeholder_layout = QVBoxLayout(placeholder_group)
        self._placeholder_table = PlaceholderTable(
            placeholders=VIDEO_JOINER_PLACEHOLDERS,
            num_columns=4,
            parent=self
        )
        self._placeholder_table.set_compact_height()
        placeholder_layout.addWidget(self._placeholder_table)
        
        # --- Command Template ---
        command_group = QGroupBox("Command Template")
        command_layout = QVBoxLayout(command_group)
        self._cmd_input = QTextEdit()
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumHeight(80)
        command_layout.addWidget(self._cmd_input)

        layout.addWidget(placeholder_group)
        layout.addWidget(command_group)

        self._placeholder_table.placeholder_double_clicked.connect(self._cmd_input.insertPlainText)

    def set_command_for_method(self, method: str):
        """Updates the command template based on the selected join method."""
        self._cmd_input.setText(self.CONCAT_DEMUXER_CMD if method == "demuxer" else self.CONCAT_FILTER_CMD)

    def get_command(self) -> str:
        """Returns the current command template from the input field."""
        return self._cmd_input.toPlainText().strip()
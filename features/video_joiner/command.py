import os
import tempfile
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QTextEdit)
from PyQt5.QtGui import QFont

from components import PlaceholderTable
from helper.placeholders import (PLACEHOLDER_INPUTFILE_NAME, PLACEHOLDER_INPUTFILE_FOLDER,
                                 PLACEHOLDER_INPUTFILE_EXT, PLACEHOLDER_OUTPUT_FOLDER,
                                 PLACEHOLDER_CONCATFILE_PATH, VIDEO_JOINER_PLACEHOLDERS
                                )

class CommandTemplate(QWidget):
    """
    A widget for managing the command template for video joining.
    It includes placeholders and a text input for the FFmpeg command.
    """
    # Default command templates for each join method
    CONCAT_DEMUXER_CMD = (f'ffmpeg -y -loglevel warning -f concat -safe 0 '
                          f'-i "{PLACEHOLDER_CONCATFILE_PATH}" '
                          f'-c copy "{PLACEHOLDER_OUTPUT_FOLDER}/joined_video.mp4"'
                        )
    inputs = ""
    filter_script = ""
    CONCAT_FILTER_CMD = (f'ffmpeg -y -loglevel warning {inputs} '
                         f'-filter_complex "{filter_script}" '
                         f'-map "[v]" -map "[a]" '
                         f'"{PLACEHOLDER_OUTPUT_FOLDER}/joined_video_re-encoded.mp4"')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cmd_input: QTextEdit
        self._setup_ui()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._cmd_input = QTextEdit()
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumHeight(80)

        layout.addWidget(self._cmd_input)

    def set_command_for_method(self, method: str):
        """Updates the command template based on the selected join method."""
        self._cmd_input.setText(self.CONCAT_DEMUXER_CMD if method == "demuxer" else self.CONCAT_FILTER_CMD)

    def get_command_template(self) -> str:
        """Returns the current command template from the input field."""
        return self._cmd_input.toPlainText().strip()

    def generate_command(self, 
                         selected_files: list[tuple[int, str, str]], 
                         output_folder: str, 
                         join_method: str) -> tuple[str | None, str | None]:
        """
        Creates the final FFmpeg command string and returns it along with any temp file path.

        Args:
            selected_files: List of files to be joined.
            output_folder: The target folder for the output.
            join_method: The method to use for joining ('demuxer' or 'filter').

        Returns:
            A tuple containing the generated command (str) and the path to the temporary
            concat file (str) if one was created, otherwise (None, None).
        """
        command_template = self.get_command_template()
        if not command_template:
            return None, None

        temp_concat_file_path = None
        replacements = {
            PLACEHOLDER_OUTPUT_FOLDER: output_folder
        }

        if join_method == "demuxer":
            concat_fd, concat_path = tempfile.mkstemp(suffix=".txt", text=True)
            with os.fdopen(concat_fd, 'w', encoding='utf-8') as f:
                for _, inputfile_name, inputfile_folder in selected_files:
                    full_path = os.path.join(inputfile_folder, inputfile_name).replace('\\', '/')
                    f.write(f"file '{full_path}'\n")
            temp_concat_file_path = concat_path
            replacements[PLACEHOLDER_CONCATFILE_PATH] = temp_concat_file_path

        for placeholder, value in replacements.items():
            command_template = command_template.replace(placeholder, value)

        return command_template, temp_concat_file_path
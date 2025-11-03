import os
import tempfile
from typing import TYPE_CHECKING
from ..base import BaseCommandTemplate

if TYPE_CHECKING:
    from .placeholders import VideoJoinerPlaceholders

class CommandTemplate(BaseCommandTemplate):
    """
    A widget for managing the command template for video joining.
    It includes placeholders and a text input for the FFmpeg command.
    """
    def __init__(self, placeholders: 'VideoJoinerPlaceholders', parent=None):
        super().__init__(parent)
        self._placeholders = placeholders
        self._CONCAT_DEMUXER_CMD = (
            f'ffmpeg -y -loglevel warning -f concat -safe 0 '
            f'-i "{self._placeholders.get_CONCATFILE_PATH()}" '
            f'-c copy "{self._placeholders.get_OUTPUT_FOLDER()}/joined_video.mp4"'
        )
        self._CONCAT_FILTER_CMD = (
            f'ffmpeg -y -loglevel warning tempvar '
            f'-filter_complex "tempvar" '
            f'-map "[v]" -map "[a]" '
            f'"{self._placeholders.get_OUTPUT_FOLDER()}/joined_video_re-encoded.mp4"'
        )

    def set_command_for_method(self, method: str):
        """Updates the command template based on the selected join method."""
        self._cmd_input.setText(self._CONCAT_DEMUXER_CMD if method == "demuxer" else self._CONCAT_FILTER_CMD)

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
        command_templates = self.get_command_template()
        if not command_templates:
            return None, None
        command_template = command_templates[0] # Video joiner only uses the first command

        replacements = {
            self._placeholders.get_OUTPUT_FOLDER(): output_folder,
            self._placeholders.get_INFILE_FOLDER(): selected_files[0][2]
        }
        temp_concat_file_path = None

        if join_method == "demuxer":
            concat_fd, concat_path = tempfile.mkstemp(suffix=".txt", text=True)
            with os.fdopen(concat_fd, 'w', encoding='utf-8') as f:
                for _, infile_name, infile_folder in selected_files:
                    full_path = os.path.join(infile_folder, infile_name).replace('\\', '/')
                    f.write(f"file '{full_path}'\n")
            temp_concat_file_path = concat_path
            replacements.update({
                self._placeholders.get_CONCATFILE_PATH(): temp_concat_file_path,
            })
        # Replace placeholders in the command template
        cmd = self._placeholders.replace_placeholders(command_template, replacements)

        return cmd, temp_concat_file_path

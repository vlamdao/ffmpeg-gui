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
        self._set_command(self._CONCAT_DEMUXER_CMD if method == "demuxer" else self._CONCAT_FILTER_CMD)

    def generate_commands(self, 
                         selected_files: list[tuple[int, str, str]], 
                         output_folder: str, 
                         join_method: str) -> tuple[str | None, str | None]:

        replacements = self._placeholders.get_replacements(input_file=selected_files[0][1], 
                                                           output_folder=output_folder, 
                                                           concatfile_path=None)
        temp_concat_file_path = None

        if join_method == "demuxer":
            temp_concat_file_path = self._create_concat_file(selected_files)
            replacements.update({
                self._placeholders.get_CONCATFILE_PATH(): temp_concat_file_path,
            })

        command_templates = self.get_command_template()
        if not command_templates:
            return None, None
        
        commands = []
        for template in command_templates:
            cmd = self._placeholders.replace_placeholders(template, replacements)
            commands.append(cmd)

        return commands, temp_concat_file_path
    
    def _create_concat_file(self, selected_files: list[tuple[int, str, str]]):
        concat_fd, concat_path = tempfile.mkstemp(suffix=".txt", text=True)
        with os.fdopen(concat_fd, 'w', encoding='utf-8') as f:
            for _, infile_name, infile_folder in selected_files:
                full_path = os.path.join(infile_folder, infile_name).replace('\\', '/')
                f.write(f"file '{full_path}'\n")

        return concat_path

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont

from .placeholders import VideoCutterPlaceholders
from ...base import BaseCommandTemplate
from helper import folder_name_ext_from_path, ms_to_time_str
from components import PlaceholdersTable

class CommandTemplate(BaseCommandTemplate):

    def __init__(self, placeholders: 'VideoCutterPlaceholders', parent=None):
        super().__init__(parent)
        self._placeholders = placeholders
        self._DEFAULT_CMD = (
            f'ffmpeg -y -loglevel warning -i "{self._placeholders.get_INFILE_FOLDER()}/{self._placeholders.get_INFILE_NAME()}.{self._placeholders.get_INFILE_EXT()}" '
            f'-ss {self._placeholders.get_START_TIME()} -to {self._placeholders.get_END_TIME()} '
            f'-c copy "{self._placeholders.get_OUTPUT_FOLDER()}/{self._placeholders.get_INFILE_NAME()}--{self._placeholders.get_SAFE_START_TIME()}--'
            f'{self._placeholders.get_SAFE_END_TIME()}.{self._placeholders.get_INFILE_EXT()}"'
        )
        
        self._set_default_cmd()
        self._cmd_input.setFixedHeight(90)

    def generate_commands(self, 
                          input_file: tuple[int, str, str], 
                          output_folder: str, 
                          start_ms: int, 
                          end_ms: int) -> str | None:
        
        infile_folder, infile_name, infile_ext = folder_name_ext_from_path(input_file)

        replacements = {
            self._placeholders.get_INFILE_FOLDER(): infile_folder,
            self._placeholders.get_INFILE_NAME(): infile_name,
            self._placeholders.get_INFILE_EXT(): infile_ext,
            self._placeholders.get_START_TIME(): str(start_ms),
            self._placeholders.get_END_TIME(): str(end_ms),
            self._placeholders.get_OUTPUT_FOLDER(): output_folder,
            self._placeholders.get_SAFE_START_TIME(): ms_to_time_str(start_ms).replace(":", "-").replace(".", "_"),
            self._placeholders.get_SAFE_END_TIME(): ms_to_time_str(end_ms).replace(":", "-").replace(".", "_"),
        }

        command_templates = self.get_command_template()
        if not command_templates:
            return None
        
        commands = []
        for template in command_templates:
            cmd = self._placeholders.replace_placeholders(template, replacements)
            commands.append(cmd)
        
        return commands
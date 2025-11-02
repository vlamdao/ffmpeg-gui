import os
from typing import TYPE_CHECKING
from components.placeholders import PlaceholderManager

if TYPE_CHECKING:
    from components import CommandInput, OutputPath

class CommandGenerator(object):
    def __init__(self, selected_files: list[tuple[int, str, str]], command_input: 'CommandInput', output_path: 'OutputPath'):
        self._selected_files = selected_files
        self._command_input = command_input
        self._output_path = output_path
        self._placeholder_manager = PlaceholderManager(output_path)

    @staticmethod
    def _finalize_command(cmd: str) -> str:
        """
        Ensures common FFmpeg flags are present in the final command.

        This method adds the following flags to the command if they are not
        already included:
        - `-y`: Overwrites output files without asking.
        - `-loglevel warning`: Reduces console output to only show warnings and errors.

        Args:
            cmd (str): The generated FFmpeg command string.

        Returns:
            str: The command string with default flags added.
        """
        if 'ffmpeg ' in cmd and '-y ' not in cmd:
            cmd = cmd.replace("ffmpeg ", "ffmpeg -y ", 1)
        if 'ffmpeg ' in cmd and '-loglevel ' not in cmd:
            cmd = cmd.replace("ffmpeg ", "ffmpeg -loglevel warning ", 1)
        return cmd
    
    def generate_command(self, input_file: tuple[int, str, str]) -> str | None:
        """Generates a command for a single-file operation."""
        if not input_file:
            return None
        
        template = self._command_input.get_command()
        # Lấy tất cả các giá trị thay thế dựa trên file đầu vào cụ thể
        replacements = self._placeholder_manager.get_general_replacements(input_file=input_file)
        cmd = self._placeholder_manager.replace(template, replacements)

        return self._finalize_command(cmd)

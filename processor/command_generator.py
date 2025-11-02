import os
from typing import TYPE_CHECKING
from helper.placeholders import (
    PLACEHOLDER_INPUTFILE_EXT, PLACEHOLDER_INPUTFILE_FOLDER,
    PLACEHOLDER_INPUTFILE_NAME, PLACEHOLDER_OUTPUT_FOLDER
)
if TYPE_CHECKING:
    from components import CommandInput, OutputPath

class CommandGenerator(object):
    def __init__(self, selected_files: list[tuple[int, str, str]], command_input: 'CommandInput', output_path: 'OutputPath'):

        self._selected_files = selected_files
        self._command_input = command_input
        self._output_path = output_path

    def _replace_placeholders(self, template: str, replacements: dict) -> str:
        """Replaces placeholders in a command template with actual values."""
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template
    
    def _get_replacement_values(self, input_file: tuple[int, str, str] | None = None) -> dict[str, str]:
        """
        Calculates and returns a dictionary of all placeholder values.
        This is the single source of truth for placeholder logic.

        Args:
            input_file (tuple | None): A tuple of (row, filename, folder) for a single file.
                                       Required for single-file operations.

        Returns:
            dict: A dictionary mapping placeholders to their calculated values.
        """

        if not input_file:
            return {}

        _, inputfile, inputfile_folder = input_file
        inputfile_name, inputfile_ext = os.path.splitext(inputfile)

        output_folder = self._output_path.get_completed_output_path(inputfile_folder)
        
        # Build the full replacement dictionary
        replacements = {
            PLACEHOLDER_INPUTFILE_FOLDER: str(inputfile_folder),
            PLACEHOLDER_INPUTFILE_NAME: str(inputfile_name),
            PLACEHOLDER_INPUTFILE_EXT: inputfile_ext.lstrip('.'),
            PLACEHOLDER_OUTPUT_FOLDER: str(output_folder),
        }
        return replacements

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
        # Get all replacements based on the specific input file
        replacements = self._get_replacement_values(input_file=input_file)
        cmd = self._replace_placeholders(template, replacements)

        return self._finalize_command(cmd)

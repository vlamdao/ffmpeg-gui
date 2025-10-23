import os
from components import CommandInput, OutputPath

# Constants for command template placeholders
PLACEHOLDER_INPUT_PATH = "{input_path}"
PLACEHOLDER_INPUT_FILE = "{input_file}"
PLACEHOLDER_OUTPUT_PATH = "{output_path}"
PLACEHOLDER_FILENAME = "{filename}"
PLACEHOLDER_EXT = "{ext}"
PLACEHOLDER_CONCAT_LIST = "{concat_list}"
PLACEHOLDER_OUTPUT = "{output}"

class CommandGenerator(object):
    def __init__(self, 
                 selected_files: list[tuple[int, str, str]], 
                 command_input: CommandInput,
                 output_path: OutputPath):

        self.selected_files = selected_files
        self.command_input = command_input
        self.output_path = output_path

    def _create_concat_file(self) -> str:
        """Creates a temporary text file listing files for FFmpeg's concat demuxer.
            Located in .temp directory in project root.
        """
        # create .temp directory in project root, same as main.py
        base_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
        temp_dir = os.path.join(base_dir, ".temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        
        # Create concat_list.txt content
        concat_content = []
        for _, fname, fpath in self.selected_files:
            full_path = os.path.join(fpath, fname)
            concat_content.append(f"file '{full_path}'")
        
        # write to concat_list.txt in .temp directory
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            f.write("\n".join(concat_content))
    
        return concat_file

    def _populate_template(self, template: str, replacements: dict) -> str:
        """Replaces placeholders in a command template with actual values."""
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template
    
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
    
    def generate_concat_command(self) -> str | None:
        """Generates the full command for a concat operation."""
        if not self.selected_files:
            return None

        _, _, inputfile_folder = self.selected_files[0]

        concat_file_path = self._create_concat_file()
        output_dir = self.output_path.get_completed_output_path(inputfile_folder, "output")
        
        template = self.command_input.get_command()
        replacements = {
            PLACEHOLDER_CONCAT_LIST: f'{concat_file_path}',
            PLACEHOLDER_OUTPUT: f'{output_dir}'
        }
        cmd = self._populate_template(template, replacements)

        return self._finalize_command(cmd)

    def generate_others_command(self, input_file: tuple[int, str, str]) -> str | None:
        """Generates a command for a single-file operation."""
        if not input_file:
            return None
        
        _, filename, inputfile_folder = input_file
        name, ext = os.path.splitext(filename)

        output_dir = self.output_path.get_completed_output_path(inputfile_folder)

        template = self.command_input.get_command()
        replacements = {
            PLACEHOLDER_INPUT_FILE: f'{os.path.join(inputfile_folder, filename)}',
            PLACEHOLDER_INPUT_PATH: f'{inputfile_folder}',
            PLACEHOLDER_OUTPUT_PATH: f'{output_dir}',
            PLACEHOLDER_FILENAME: name,
            PLACEHOLDER_EXT: ext.lstrip('.')
        }
        cmd = self._populate_template(template, replacements)

        return self._finalize_command(cmd)

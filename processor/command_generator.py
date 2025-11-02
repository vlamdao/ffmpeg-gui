from components import Placeholders

class CommandGenerator():
    def __init__(self):
        self._placeholders = Placeholders()

    def _finalize_command(self, cmd: str) -> str:
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
    
    def generate_command(self, input_file: str, output_folder: str, command_template: str) -> str | None:
        """Generates a command for a single-file operation."""
        if not input_file:
            return None
        
        replacements = self._placeholders.get_replacements(input_file, output_folder)
        cmd = self._placeholders.replace_placeholders(command_template, replacements)

        return self._finalize_command(cmd)

from components import Placeholders

class CommandGenerator():
    def __init__(self):
        self._placeholders = Placeholders()

    def _finalize_command(self, cmd: str) -> str:
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

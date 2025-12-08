from .placeholders import VideoCutterPlaceholders
from features.base import BaseCommandTemplate

class CommandTemplate(BaseCommandTemplate):

    def __init__(self, placeholders: 'VideoCutterPlaceholders', parent=None):
        super().__init__(parent)
        self._placeholders = placeholders
        self._DEFAULT_CMD = (
            f'ffmpeg -y -loglevel info -i "{self._placeholders.get_INFILE_FOLDER()}/{self._placeholders.get_INFILE_NAME()}.{self._placeholders.get_INFILE_EXT()}" '
            f'-ss {self._placeholders.get_START_TIME()} -to {self._placeholders.get_END_TIME()} '
            f'-c copy "{self._placeholders.get_OUTPUT_FOLDER()}/{self._placeholders.get_INFILE_NAME()}--{self._placeholders.get_SAFE_START_TIME()}--'
            f'{self._placeholders.get_SAFE_END_TIME()}.{self._placeholders.get_INFILE_EXT()}"'
        )
        
        self._set_default_cmd()

    def generate_commands(self, 
                          input_file: tuple[int, str, str], 
                          output_folder: str, 
                          start_ms: int, 
                          end_ms: int) -> str | None:
        
        replacements = self._placeholders.get_replacements(input_file=input_file, 
                                                           output_folder=output_folder, 
                                                           start_ms=start_ms, 
                                                           end_ms=end_ms)
        
        command_templates = self.get_command_template()
        if not command_templates:
            return None
        
        commands = []
        for template in command_templates:
            cmd = self._placeholders.replace_placeholders(template, replacements)
            commands.append(cmd)
        
        return commands
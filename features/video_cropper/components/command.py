from features.base import BaseCommandTemplate

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .placeholders import VideoCropperPlaceholders

class VideoCropperCommandTemplate(BaseCommandTemplate):

    def __init__(self, placeholders: 'VideoCropperPlaceholders', parent=None):
        super().__init__(parent)
        self._placeholders = placeholders

        self._DEFAULT_CMD = [
            f'ffmpeg -y -loglevel info '
            f'-ss {self._placeholders.get_START_TIME()} -to {self._placeholders.get_END_TIME()} '
            f'-i "{self._placeholders.get_INFILE_FOLDER()}/{self._placeholders.get_INFILE_NAME()}.{self._placeholders.get_INFILE_EXT()}" '
            f'-vf "crop={self._placeholders.get_CROP_WIDTH()}:{self._placeholders.get_CROP_HEIGHT()}:{self._placeholders.get_CROP_X()}:{self._placeholders.get_CROP_Y()}" '
            f'-c:v libx264 -preset veryfast '
            f'"{self._placeholders.get_OUTPUT_FOLDER()}/{self._placeholders.get_INFILE_NAME()}_cropped.{self._placeholders.get_INFILE_EXT()}"'
        ]
        self._set_default_cmd()
        
    def generate_commands(self,
                          input_file: str,
                          output_folder: str,
                          crop_params: dict,
                          start_time: str,
                          end_time: str) -> list[str] | None:
        """Generates the FFmpeg command for cropping."""

        replacements = self._placeholders.get_replacements(input_file=input_file,
                                                          output_folder=output_folder,
                                                          crop_params=crop_params,
                                                          start_time=start_time,
                                                          end_time=end_time)

        command_templates = self.get_command_template()
        if not command_templates:
            return None

        commands = [self._placeholders.replace_placeholders(template, replacements)
                    for template in command_templates]

        return commands
import os
from helper import styled_text
from features.base import BaseProcessor

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .components import CommandTemplate

class VideoJoinerProcessor(BaseProcessor):
    """
    Handles the background processing for joining videos using FFmpeg.
    """


    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp_concat_file_path: str | None = None

    def _prepare_job(self,
              selected_files: list[tuple[int, str, str]], 
              output_folder: str, 
              cmd_template: 'CommandTemplate', 
              join_method: str) -> tuple[list[tuple[str, list[str]]], str]:

        # Ensure the output directory exists before generating commands that use it.
        os.makedirs(output_folder, exist_ok=True)

        commands, self._temp_concat_file_path = cmd_template.generate_commands(selected_files, output_folder, join_method)
        if not commands:
            return None, styled_text('bold', 'red', None, f'Features: {self.get_feature_name()} | '
                                                        f'Could not generate command. Check the command template.')
        
        outputfile_path = commands[-1].split('"')[-2] if commands else None
        job = [("video_joiner_job", commands, outputfile_path)]
        message = styled_text('bold', 'blue', None, f"Features: {self.get_feature_name()} | "
                                                 f"Starting to join {len(selected_files)} files...")
        return (job, message)
    
    def get_feature_name(self) -> str:
        return "Video Joiner"

    def _cleanup(self):
        if self._temp_concat_file_path and os.path.exists(self._temp_concat_file_path):
            try:
                os.remove(self._temp_concat_file_path)
                self.log_signal.emit(styled_text('bold', 'green', None, f'Features: {self.get_feature_name()} | '
                                                 f'cleaned up temporary file: {self._temp_concat_file_path}'))
            except OSError as e:
                self.log_signal.emit(styled_text('bold', 'red', None, f"Features: {self.get_feature_name()} | "
                                                 f"Error removing temporary file: {e}"))
        self._temp_concat_file_path = None
        super()._cleanup()
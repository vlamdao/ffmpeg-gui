import os
from typing import TYPE_CHECKING
from helper import styled_text
from ..base import BaseProcessor

class VideoJoinerProcessor(BaseProcessor):
    """
    Handles the background processing for joining videos using FFmpeg.
    """
    if TYPE_CHECKING:
        from .command import CommandTemplate

    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp_concat_file_path: str | None = None

    def _prepare_job(self,
              selected_files: list[tuple[int, str, str]], 
              output_folder: str, 
              cmd_template: 'CommandTemplate', 
              join_method: str) -> tuple[list[tuple[str, list[str]]], str]:
        
        commands, self._temp_concat_file_path = cmd_template.generate_commands(selected_files, output_folder, join_method)
        job = [("video_joiner_job", commands)]
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
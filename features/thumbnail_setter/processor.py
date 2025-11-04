import os
from helper import styled_text
from features.base import BaseProcessor

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .components import CommandTemplates

class ThumbnailProcessor(BaseProcessor):
    """
    Handles the background processing for setting a video thumbnail using FFmpeg.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp_thumb_path: str | None = None

    def _prepare_job(self, 
                     input_file: str, 
                     output_folder: str, 
                     cmd_template: 'CommandTemplates',
                     timestamp: str) -> tuple[list[tuple[str, list[str]]], str]:
        
        # Ensure the output directory exists before generating commands that use it.
        os.makedirs(output_folder, exist_ok=True)

        commands, self._temp_thumb_path = cmd_template.generate_commands(input_file=input_file, 
                                                                         output_folder=output_folder, 
                                                                         timestamp=timestamp)
        if not commands:
            return None, styled_text('bold', 'red', None, f'Features: {self.get_feature_name()} | '
                                                        f'Could not generate command. Check the command template.')
                                                        
        job = [("thumbnail_setter_job", commands)]
        message = styled_text('bold', 'blue', None, f"Features: {self.get_feature_name()} | "
                                                 f"Starting to set thumbnail for '{os.path.basename(input_file)}' at {timestamp}...")
        return (job, message)
    
    def get_feature_name(self):
        return "Thumbnail Setter"
    
    def _cleanup(self):
        """Cleans up resources after the worker thread has completely finished."""
        if self._temp_thumb_path and os.path.exists(self._temp_thumb_path):
            try:
                os.remove(self._temp_thumb_path)
                self.log_signal.emit(styled_text('bold', 'green', None, f'Features: {self.get_feature_name()} | '
                                         f'cleaned up temporary file: {self._temp_thumb_path}'))
            except OSError as e:
                self.log_signal.emit(styled_text('bold', 'red', None, f"Features: {self.get_feature_name()} | "
                                         f"Error removing temporary file: {e}"))
        self._temp_thumb_path = None
        super()._cleanup()

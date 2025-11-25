import os
from helper import styled_text
from features.base import BaseProcessor

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .components import CommandTemplate

class VideoCropperProcessor(BaseProcessor):
    """
    Handles the background processing for cropping a video using FFmpeg.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def get_feature_name(self) -> str:
        return "Video Cropper"

    def _prepare_job(self,
                     input_file: str,
                     output_folder: str,
                     cmd_template: 'CommandTemplate',
                     crop_params: dict) -> tuple[list[tuple[str, list[str], str]] | None, str | None]:

        os.makedirs(output_folder, exist_ok=True)

        commands = cmd_template.generate_commands(input_file=input_file,
                                                  output_folder=output_folder,
                                                  crop_params=crop_params)
        if not commands:
            return None, styled_text('bold', 'red', None, f'Features: {self.get_feature_name()} | '
                                                        f'Could not generate command. Check the command template.')

        outputfile_path = commands[-1].split('"')[-2] if commands else None
        job_id = f"crop_{os.path.basename(input_file)}"
        job = [(job_id, commands, outputfile_path)]
        message = styled_text('bold', 'blue', None, f"Features: {self.get_feature_name()} | "
                                                 f"Starting to crop '{os.path.basename(input_file)}'...")
        return (job, message)
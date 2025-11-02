import os
from typing import TYPE_CHECKING

from .definitions import (
    PLACEHOLDER_INPUTFILE_EXT, PLACEHOLDER_INPUTFILE_FOLDER,
    PLACEHOLDER_INPUTFILE_NAME, PLACEHOLDER_OUTPUT_FOLDER
)

if TYPE_CHECKING:
    from ..output_path import OutputPath

class PlaceholderManager:
    """
    Lớp cơ sở để quản lý và lấy giá trị cho các placeholders.
    Đây là nguồn sự thật duy nhất cho logic placeholder chung.
    """
    def __init__(self, output_path_obj: 'OutputPath'):
        self._output_path = output_path_obj

    def get_general_replacements(self, input_file: tuple[int, str, str]) -> dict[str, str]:
        """
        Tạo ra các giá trị thay thế cho các placeholder chung dựa trên một file đầu vào.

        Args:
            input_file (tuple): Một tuple chứa (row, filename, folder) cho một file.

        Returns:
            dict: Một dictionary ánh xạ các placeholder chung tới giá trị của chúng.
        """
        if not input_file:
            return {}

        _, inputfile, inputfile_folder = input_file
        inputfile_name, inputfile_ext = os.path.splitext(inputfile)

        output_folder = self._output_path.get_completed_output_path(inputfile_folder)

        replacements = {
            PLACEHOLDER_INPUTFILE_FOLDER: str(inputfile_folder),
            PLACEHOLDER_INPUTFILE_NAME: str(inputfile_name),
            PLACEHOLDER_INPUTFILE_EXT: inputfile_ext.lstrip('.'),
            PLACEHOLDER_OUTPUT_FOLDER: str(output_folder),
        }
        return replacements

    def replace(self, template: str, replacements: dict) -> str:
        """Thay thế các placeholder trong một chuỗi mẫu."""
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template
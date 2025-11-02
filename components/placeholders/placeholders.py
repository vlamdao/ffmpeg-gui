import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..output_path import OutputPath


class Placeholders:
    def __init__(self):
        self.INPUTFILE_FOLDER = "{inputfile_folder}"
        self.INPUTFILE_NAME = "{inputfile_name}"
        self.INPUTFILE_EXT = "{inputfile_ext}"
        self.OUTPUT_FOLDER = "{output_folder}"

        self.GENERAL_PLACEHOLDERS = [
            self.INPUTFILE_FOLDER,
            self.INPUTFILE_NAME,
            self.INPUTFILE_EXT,
            self.OUTPUT_FOLDER,
        ]

    def get_placeholders_list(self):
        return self.GENERAL_PLACEHOLDERS
    
    def get_replacements(self, input_file:  tuple[int, str, str], output_path: 'OutputPath'):
        if not input_file:
            return {}

        _, inputfile, inputfile_folder = input_file
        inputfile_name, inputfile_ext = os.path.splitext(inputfile)
        output_folder = output_path.get_completed_output_path(inputfile_folder)

        replacements = {
            self.INPUTFILE_FOLDER: str(inputfile_folder),
            self.INPUTFILE_NAME: str(inputfile_name),
            self.INPUTFILE_EXT: inputfile_ext.lstrip('.'),
            self.OUTPUT_FOLDER: str(output_folder),
        }
        return replacements

    def replace(self, template: str, replacements: dict) -> str:
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template
        
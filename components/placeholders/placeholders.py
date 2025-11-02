import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..output_path import OutputPath


class Placeholders:
    def __init__(self):
        self._INPUTFILE_FOLDER = "{inputfile_folder}"
        self._INPUTFILE_NAME = "{inputfile_name}"
        self._INPUTFILE_EXT = "{inputfile_ext}"
        self._OUTPUT_FOLDER = "{output_folder}"

    def get_INPUTFILE_FOLDER(self):
        return self._INPUTFILE_FOLDER
    
    def get_INPUTFILE_NAME(self):
        return self._INPUTFILE_NAME
    
    def get_INPUTFILE_EXT(self):
        return self._INPUTFILE_EXT
    
    def get_OUTPUT_FOLDER(self):
        return self._OUTPUT_FOLDER
    
    def get_placeholders_list(self):
        return [self._INPUTFILE_FOLDER, self._INPUTFILE_NAME, self._INPUTFILE_EXT, self._OUTPUT_FOLDER]
    
    def get_replacements(self, input_file:  tuple[int, str, str], output_path: 'OutputPath'):
        if not input_file:
            return {}

        _, inputfile, inputfile_folder = input_file
        inputfile_name, inputfile_ext = os.path.splitext(inputfile)
        output_folder = output_path.get_completed_output_path(inputfile_folder)

        replacements = {
            self._INPUTFILE_FOLDER: str(inputfile_folder),
            self._INPUTFILE_NAME: str(inputfile_name),
            self._INPUTFILE_EXT: inputfile_ext.lstrip('.'),
            self._OUTPUT_FOLDER: str(output_folder),
        }
        return replacements

    def replace(self, template: str, replacements: dict) -> str:
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template
        
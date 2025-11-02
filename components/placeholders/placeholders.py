import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..output_folder import OutputFolder


class Placeholders:
    def __init__(self):
        self._INPUTFILE_FOLDER = "{infile_folder}"
        self._INPUTFILE_NAME = "{infile_name}"
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
    
    def get_replacements(self, input_file: str, output_folder: str):
        if not input_file:
            return {}

        infile_folder = os.path.dirname(input_file)
        filename = os.path.basename(input_file)
        infile_name, inputfile_ext = os.path.splitext(filename)
        
        replacements = {
            self._INPUTFILE_FOLDER: str(infile_folder),
            self._INPUTFILE_NAME: str(infile_name),
            self._INPUTFILE_EXT: inputfile_ext.lstrip('.'),
            self._OUTPUT_FOLDER: str(output_folder),
        }
        return replacements

    def replace_placeholders(self, template: str, replacements: dict) -> str:
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template
        
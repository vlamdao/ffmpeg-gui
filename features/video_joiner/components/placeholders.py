from components import Placeholders

class VideoJoinerPlaceholders(Placeholders):
    def __init__(self):
        super().__init__()
        self._CONCATFILE_PATH = "{concatfile_path}"
    
    def get_CONCATFILE_PATH(self):
        return self._CONCATFILE_PATH
    
    def get_placeholders_list(self):
        return super().get_placeholders_list() + [self._CONCATFILE_PATH]
    
    def get_replacements(self, 
                         input_file: str, 
                         output_folder: str,
                         concatfile_path: str):
        replacements = super().get_replacements(input_file, output_folder)
        replacements.update({
            self._CONCATFILE_PATH: concatfile_path,
        })
        return replacements
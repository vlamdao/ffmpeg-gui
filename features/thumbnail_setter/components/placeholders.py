from components import Placeholders

class ThumbnailPlaceholders(Placeholders):
    def __init__(self):
        super().__init__()
        self._TIMESTAMP = "{timestamp}"
        self._THUMB_PATH = "{thumb_path}"
    
    def get_TIMESTAMP(self):
        return self._TIMESTAMP
    
    def get_THUMB_PATH(self):
        return self._THUMB_PATH
    
    def get_placeholders_list(self):
        return super().get_placeholders_list() + [self._TIMESTAMP] + [self._THUMB_PATH]
    
    def get_replacements(self, input_file, output_folder, timestamp, thumb_path):
        replacements = super().get_replacements(input_file, output_folder)
        replacements.update({
            self._TIMESTAMP: timestamp,
            self._THUMB_PATH: thumb_path,
        })
        return replacements
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components import OutputPath

from components import Placeholders
from helper import ms_to_time_str


class VideoCutterPlaceholders(Placeholders):
    def __init__(self):
        super().__init__()
        self._START_TIME = "{start_time}"
        self._END_TIME = "{end_time}"
        self._SAFE_START_TIME = "{safe_start_time}"
        self._SAFE_END_TIME = "{safe_end_time}"
    
    def get_START_TIME(self):
        return self._START_TIME
    
    def get_END_TIME(self):
        return self._END_TIME
    
    def get_SAFE_START_TIME(self):
        return self._SAFE_START_TIME
    
    def get_SAFE_END_TIME(self):
        return self._SAFE_END_TIME
    
    def get_placeholders_list(self):
        return super().get_placeholders_list() + [
            self._START_TIME, self._END_TIME, self._SAFE_START_TIME, self._SAFE_END_TIME
        ]
    
    def get_replacements(self, 
                         input_file: tuple[int, str, str], 
                         output_path: 'OutputPath',
                         start_ms: int, 
                         end_ms: int):
        replacements = super().get_replacements(input_file, output_path)
        replacements.update({
            self._START_TIME: ms_to_time_str(start_ms),
            self._END_TIME: ms_to_time_str(end_ms),
            self._SAFE_START_TIME: ms_to_time_str(start_ms).replace(":", "-").replace(".", "_"),
            self._SAFE_END_TIME: ms_to_time_str(end_ms).replace(":", "-").replace(".", "_"),
        })
        return replacements
from components import Placeholders

class VideoCropperPlaceholders(Placeholders):
    def __init__(self):
        super().__init__()
        self._CROP_WIDTH = "{crop_width}"
        self._CROP_HEIGHT = "{crop_height}"
        self._CROP_X = "{crop_x}"
        self._CROP_Y = "{crop_y}"
        self._START_TIME = "{start_time}"
        self._END_TIME = "{end_time}"

    def get_CROP_WIDTH(self): return self._CROP_WIDTH
    def get_CROP_HEIGHT(self): return self._CROP_HEIGHT
    def get_CROP_X(self): return self._CROP_X
    def get_CROP_Y(self): return self._CROP_Y
    def get_START_TIME(self): return self._START_TIME
    def get_END_TIME(self): return self._END_TIME

    def get_placeholders_list(self):
        return super().get_placeholders_list() + [
            self._CROP_WIDTH,
            self._CROP_HEIGHT,
            self._CROP_X,
            self._CROP_Y,
            self._START_TIME,
            self._END_TIME
        ]

    def get_replacements(self, input_file, output_folder, crop_params, start_time, end_time):
        replacements = super().get_replacements(input_file, output_folder)
        replacements.update({
            self._CROP_WIDTH: crop_params['w'],
            self._CROP_HEIGHT: crop_params['h'],
            self._CROP_X: crop_params['x'],
            self._CROP_Y: crop_params['y'],
            self._START_TIME: start_time,
            self._END_TIME: end_time,
        })
        return replacements
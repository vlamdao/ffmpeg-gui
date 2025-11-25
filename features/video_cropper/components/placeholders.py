from components import Placeholders

class VideoCropperPlaceholders(Placeholders):
    def __init__(self):
        super().__init__()
        self._CROP_WIDTH = "{crop_width}"
        self._CROP_HEIGHT = "{crop_height}"
        self._CROP_X = "{crop_x}"
        self._CROP_Y = "{crop_y}"

    def get_CROP_WIDTH(self): return self._CROP_WIDTH
    def get_CROP_HEIGHT(self): return self._CROP_HEIGHT
    def get_CROP_X(self): return self._CROP_X
    def get_CROP_Y(self): return self._CROP_Y

    def get_placeholders_list(self):
        return super().get_placeholders_list() + [
            self._CROP_WIDTH,
            self._CROP_HEIGHT,
            self._CROP_X,
            self._CROP_Y
        ]

    def get_replacements(self, input_file, output_folder, crop_params):
        replacements = super().get_replacements(input_file, output_folder)
        replacements.update({
            self._CROP_WIDTH: crop_params['w'],
            self._CROP_HEIGHT: crop_params['h'],
            self._CROP_X: crop_params['x'],
            self._CROP_Y: crop_params['y'],
        })
        return replacements
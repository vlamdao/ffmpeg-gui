from features.base import ActionButtons

class ActionPanel(ActionButtons):
    """
    A specialized set of action buttons for the Video Cropper feature.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_widgets(self):
        super()._create_widgets()
        self.set_run_button_text(" Crop Video")
        self._run_button.set_icon("crop-video.png")

    def update_ui_state(self, state: str):
        """
        Enables or disables UI controls based on the processing state.

        Args:
            state (str): The current state, either "enable" or "disable".
        """
        if state == "enable":
            self.enable_run_button()
            self.disable_stop_button()
        elif state == "disable":
            self.disable_run_button()
            self.enable_stop_button()
        else:
            return
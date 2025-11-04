from features.base import ActionButtons
from PyQt5.QtCore import Qt

class ActionPanel(ActionButtons):

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_widgets(self):
        super()._create_widgets()
        
        self.set_run_button_text("Join Videos ")
        self._run_button.set_layout_direction(Qt.RightToLeft)
        self._run_button.set_icon("run-join-video.png")

    def _setup_layout(self):
        super()._setup_layout()
    
    def update_ui_state(self, state: str):
        if state == "enable":
            self.enable_run_button()
            self.disable_stop_button()
        elif state == "disable":
            self.disable_run_button()
            self.enable_stop_button()
        else:
            return
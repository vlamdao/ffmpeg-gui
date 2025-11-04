from ..base import ActionButtons
from PyQt5.QtWidgets import (QLineEdit, QPushButton, QHBoxLayout)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from components import StyledButton
from helper import resource_path

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
    
    def disable_action_panel(self, is_disable: bool):
        self.disable_run_button(is_disable)
        self.disable_stop_button(not is_disable)
from ...base import ActionButtons
from PyQt5.QtWidgets import (QLineEdit, QPushButton, QHBoxLayout)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from components import StyledButton
from helper import resource_path

class ActionPanel(ActionButtons):

    set_start_clicked = pyqtSignal()
    set_end_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_widgets(self):
        super()._create_widgets()

        self.set_run_button_text(" Cut Segments")
        self._run_button.set_icon("cut-segments.png")

        self._set_start_button = StyledButton(
            text=" Set Start",
            icon_name="set-start.png",
            icon_size=self._ICON_SIZE,
            min_height=self._BUTTON_MIN_HEIGHT
        )
        self._set_end_button = StyledButton(
            text="Set End ",
            icon_name="set-end.png",
            icon_size=self._ICON_SIZE,
            min_height=self._BUTTON_MIN_HEIGHT,
            layout_direction=Qt.RightToLeft
        )

    def _setup_layout(self):
        super()._setup_layout()
        
        self.layout.insertWidget(1, self._set_start_button)
        self.layout.insertWidget(2, self._set_end_button)
        
    def _connect_signals(self):
        super()._connect_signals()
        
        self._set_start_button.clicked.connect(self.set_start_clicked)
        self._set_end_button.clicked.connect(self.set_end_clicked)
        
    def update_ui_state(self, state: str):
        if state == "enable":
            self._set_start_button.setEnabled(True)
            self._set_end_button.setEnabled(True)
            self.enable_run_button()
            self.disable_stop_button()
        elif state == "disable":
            self._set_start_button.setDisabled(True)
            self._set_end_button.setDisabled(True)
            self.disable_run_button()
            self.enable_stop_button()
        else:
            return

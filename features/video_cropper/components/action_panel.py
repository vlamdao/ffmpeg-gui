from features.base import ActionButtons
from components import StyledButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

class ActionPanel(ActionButtons):
    """
    A specialized set of action buttons for the Video Cropper feature.
    """
    set_start_clicked = pyqtSignal()
    set_end_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_widgets(self):
        super()._create_widgets()

        self.set_run_button_text(" Crop Video")
        self._run_button.set_icon("crop-video.png")

        self._start_time_edit = QLineEdit("00:00:00.000")
        self._start_time_edit.setFont(QFont("Consolas", 9))
        self._start_time_edit.setAlignment(Qt.AlignCenter)
        self._start_time_edit.setMinimumHeight(self._BUTTON_MIN_HEIGHT - 4)

        self._end_time_edit = QLineEdit("00:00:00.000")
        self._end_time_edit.setFont(QFont("Consolas", 9))
        self._end_time_edit.setAlignment(Qt.AlignCenter)
        self._end_time_edit.setMinimumHeight(self._BUTTON_MIN_HEIGHT - 4)

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
        self.layout.insertWidget(2, self._start_time_edit)
        self.layout.insertWidget(3, self._end_time_edit)
        self.layout.insertWidget(4, self._set_end_button)

    def _connect_signals(self):
        super()._connect_signals()
        self._set_start_button.clicked.connect(self.set_start_clicked)
        self._set_end_button.clicked.connect(self.set_end_clicked)

    def update_ui_state(self, state: str):
        """
        Enables or disables UI controls based on the processing state.

        Args:
            state (str): The current state, either "enable" or "disable".
        """
        if state == "enable":
            self.enable_run_button()
            self.disable_stop_button()
            self._set_start_button.setEnabled(True)
            self._set_end_button.setEnabled(True)
            self._start_time_edit.setEnabled(True)
            self._end_time_edit.setEnabled(True)
        elif state == "disable":
            self.disable_run_button()
            self.enable_stop_button()
            self._set_start_button.setDisabled(True)
            self._set_end_button.setDisabled(True)
            self._start_time_edit.setDisabled(True)
            self._end_time_edit.setDisabled(True)
        else:
            return

    def get_start_time(self) -> str:
        return self._start_time_edit.text()

    def get_end_time(self) -> str:
        return self._end_time_edit.text()

    def set_start_time(self, time_str: str): self._start_time_edit.setText(time_str)
    def set_end_time(self, time_str: str): self._end_time_edit.setText(time_str)
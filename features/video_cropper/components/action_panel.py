from features.base import BaseActionPanel
from components import StyledButton, buttons
from PyQt5.QtWidgets import QLineEdit, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

class VideoCropperActionPanel(BaseActionPanel):
    """
    A specialized set of action buttons for the Video Cropper feature.
    """
    set_start_clicked = pyqtSignal()
    set_end_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_widgets(self):
        super()._create_widgets()

        self._segment_label = QLabel("00:00:00.000 - 00:00:00.000")
        self._segment_label.setFont(QFont("Consolas", 9))
        self._segment_label.setAlignment(Qt.AlignCenter)

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
        self.layout.insertWidget(1, self._segment_label)
        self.layout.insertWidget(2, self._set_start_button)
        self.layout.insertWidget(3, self._set_end_button)

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
        super().update_ui_state(state)

        if state == "enable":
            self._set_start_button.setEnabled(True)
            self._set_end_button.setEnabled(True)
        elif state == "disable":
            self._set_start_button.setDisabled(True)
            self._set_end_button.setDisabled(True)
        else:
            return

    def set_segment_label(self, segment_str: str):
        self._segment_label.setText(segment_str)
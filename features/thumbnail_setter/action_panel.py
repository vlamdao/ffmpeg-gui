from ..base import ActionButtons
from PyQt5.QtWidgets import (QLineEdit, QPushButton, QHBoxLayout)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from components import StyledButton
from helper import resource_path

class ActionPanel(ActionButtons):

    go_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_widgets(self):
        super()._create_widgets()

        self.set_run_button_text(" Set Thumbnail")
        self._run_button.set_icon("run-set-thumbnail.png")

        self._timestamp_edit = QLineEdit()
        self._timestamp_edit.setInputMask("00:00:00.000")
        self._timestamp_edit.setText("00:00:00.000")
        self._timestamp_edit.setFixedWidth(120)
        self._timestamp_edit.setMinimumHeight(self._BUTTON_MIN_HEIGHT - 4)
        self._timestamp_edit.setFont(QFont("Consolas", 9))
        self._timestamp_edit.setAlignment(Qt.AlignCenter)
        
        self._go_to_button = StyledButton(
            text="Go ",
            icon_name="go.png",
            icon_size=self._ICON_SIZE,
            min_height=self._BUTTON_MIN_HEIGHT,
            layout_direction=Qt.RightToLeft
        )

    def _setup_layout(self):
        super()._setup_layout()

        self.layout.insertWidget(1, self._timestamp_edit)
        self.layout.insertWidget(2, self._go_to_button)

    def _connect_signals(self):
        super()._connect_signals()
        self._go_to_button.clicked.connect(self.go_clicked)

    def get_timestamp_text(self) -> str:
        return self._timestamp_edit.text()
    
    def set_custom_controls_enabled(self, is_enabled: bool):
        self._timestamp_edit.setEnabled(is_enabled)
        self._go_to_button.setEnabled(is_enabled)

    def set_processing_state(self, is_processing: bool):
        """Ánh xạ tới phương thức set_enable của lớp cha."""
        self.set_enable(not is_processing)

        
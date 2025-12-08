from components import StyledButton
from PyQt5.QtWidgets import (QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize

class ActionButtons(QWidget):
    _BUTTON_MIN_HEIGHT = 36
    _ICON_SIZE = QSize(20, 20)
    _BUTTON_PADDING = (16, 0, 16, 0)

    run_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._run_button: StyledButton
        self._stop_button: StyledButton

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        self._run_button = StyledButton(text=" Run",
                                        icon_name="run.png",
                                        icon_size=self._ICON_SIZE,
                                        padding=self._BUTTON_PADDING,
                                        min_height=self._BUTTON_MIN_HEIGHT,
                                        )
        self._stop_button = StyledButton(text=" Stop",
                                         icon_name="stop.png",
                                         icon_size=self._ICON_SIZE,
                                         min_height=self._BUTTON_MIN_HEIGHT,
                                         )

    def _setup_layout(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addStretch()
        self.layout.addWidget(self._run_button)
        self.layout.addWidget(self._stop_button)

    def _connect_signals(self):
        self._run_button.clicked.connect(self.run_clicked)
        self._stop_button.clicked.connect(self.stop_clicked)

    def disable_run_button(self):
        self._run_button.setDisabled(True)

    def disable_stop_button(self):
        self._stop_button.setDisabled(True)
    
    def enable_run_button(self):
        self._run_button.setEnabled(True)

    def enable_stop_button(self):
        self._stop_button.setEnabled(True)

    def set_run_button_text(self, text: str):
        self._run_button.setText(text)

    def set_stop_button_text(self, text: str):
        self._stop_button.setText(text)
    
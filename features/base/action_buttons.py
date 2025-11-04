from components import StyledButton
from PyQt5.QtWidgets import (QVBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize

class ActionButtons():

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
        self._run_button = StyledButton(text="Run",
                                        icon_name="run.png",
                                        icon_size=QSize(20, 20),
                                        )
        self._stop_button = StyledButton(text="Stop",
                                         icon_name="stop.png",
                                         icon_size=QSize(20, 20),
                                         )

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._run_button)
        layout.addWidget(self._stop_button)

    def _connect_signals(self):
        self._run_button.clicked.connect(self.run_clicked)
        self._stop_button.clicked.connect(self.stop_clicked)

    def set_enable(self, is_enable: bool):
        self._run_button.setEnabled(is_enable)
        self._stop_button.setEnabled(not is_enable)
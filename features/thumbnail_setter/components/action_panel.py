from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from components import StyledButton
from features.base import ActionButtons

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

    def update_ui_state(self, state: str):
        if state == "enable":
            self.enable_run_button()
            self.disable_stop_button()
            self._timestamp_edit.setEnabled(True)
            self._go_to_button.setEnabled(True)
        elif state == "disable":
            self.disable_run_button()
            self.enable_stop_button()
            self._timestamp_edit.setDisabled(True)
            self._go_to_button.setDisabled(True)
        else:
            return


        
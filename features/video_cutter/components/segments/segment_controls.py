from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy, QStyle)
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon

from helper import ms_to_time_str, resource_path

class SegmentControls(QWidget):
    """A widget containing the main controls for creating and processing segments.

    This encapsulated widget provides buttons for setting start/end times and
    initiating the cut process, along with labels to display the current times.
    It communicates user actions to the parent widget via signals.
    """

    # --- Public Signals ---
    set_start_clicked = pyqtSignal()
    """Emitted when the 'Set Start' button is clicked."""
    set_end_clicked = pyqtSignal()
    """Emitted when the 'Set End' button is clicked."""
    cut_clicked = pyqtSignal()
    """Emitted when the 'Cut Segments' button is clicked."""
    stop_clicked = pyqtSignal()
    """Emitted when the 'Stop' button is clicked."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Internal widgets, prefixed with _
        self._set_start_button: QPushButton
        self._set_end_button: QPushButton
        self._cut_button: QPushButton
        self._stop_button: QPushButton
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Creates the individual widgets for the controls."""
        icon_size = QSize(20, 20)
        min_height = 36

        self._set_start_button = QPushButton(" Set Start")
        self._set_start_button.setIcon(QIcon(resource_path("icon/set-start.png")))
        self._set_start_button.setIconSize(icon_size)
        self._set_start_button.setMinimumHeight(min_height)

        self._set_end_button = QPushButton("Set End ")
        self._set_end_button.setIcon(QIcon(resource_path("icon/set-end.png")))
        self._set_end_button.setIconSize(icon_size)
        self._set_end_button.setLayoutDirection(Qt.RightToLeft)
        self._set_end_button.setMinimumHeight(min_height)

        self._cut_button = QPushButton(" Cut Segments")
        self._cut_button.setIcon(QIcon(resource_path("icon/cut-segments.png")))
        self._cut_button.setIconSize(icon_size)
        self._cut_button.setStyleSheet("padding-left: 12px; padding-right: 12px;")
        self._cut_button.setMinimumHeight(min_height)

        self._stop_button = QPushButton(" Stop")
        self._stop_button.setIcon(QIcon(resource_path("icon/stop.png")))
        self._stop_button.setIconSize(icon_size)
        self._stop_button.setMinimumHeight(min_height)

    def _setup_layout(self):
        """Sets up the layout for the controls."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._set_start_button)
        layout.addWidget(self._set_end_button)
        layout.addStretch(1)
        layout.addWidget(self._cut_button)
        layout.addWidget(self._stop_button)
        
    def _connect_signals(self):
        """Connects internal widget signals to the public signals of this class."""
        self._set_start_button.clicked.connect(self.set_start_clicked)
        self._set_end_button.clicked.connect(self.set_end_clicked)
        self._cut_button.clicked.connect(self.cut_clicked)
        self._stop_button.clicked.connect(self.stop_clicked)

    def set_enable(self, is_enable: bool):
        """Sets the enabled state of buttons based on processing status."""
        self._set_start_button.setEnabled(is_enable)
        self._set_end_button.setEnabled(is_enable)
        self._cut_button.setEnabled(is_enable)
        # self._stop_button.setEnabled(is_enable)
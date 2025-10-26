from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy)
from PyQt5.QtCore import pyqtSignal

from helper import ms_to_time_str

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
    close_clicked = pyqtSignal()
    """Emitted when the 'Close' button is clicked."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Internal widgets, prefixed with _
        self._set_start_button: QPushButton
        self._set_end_button: QPushButton
        self._cut_button: QPushButton
        self._close_button: QPushButton
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Creates the individual widgets for the controls."""
        self._set_start_button = QPushButton("Set Start")
        self._set_end_button = QPushButton("Set End")
        self._cut_button = QPushButton("Cut Segments")
        self._close_button = QPushButton("Close")

    def _setup_layout(self):
        """Sets up the layout for the controls."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._set_start_button)
        layout.addWidget(self._set_end_button)
        layout.addStretch()
        layout.addWidget(self._cut_button)
        layout.addWidget(self._close_button)

    def _connect_signals(self):
        """Connects internal widget signals to the public signals of this class."""
        self._set_start_button.clicked.connect(self.set_start_clicked)
        self._set_end_button.clicked.connect(self.set_end_clicked)
        self._cut_button.clicked.connect(self.cut_clicked)
        self._close_button.clicked.connect(self.close_clicked)
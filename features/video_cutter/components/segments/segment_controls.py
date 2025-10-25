from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy)
from PyQt5.QtCore import pyqtSignal

from helper import ms_to_time_str

class SegmentControls(QWidget):
    _DEFAULT_START_TEXT = "Start: --:--:--.---"
    _DEFAULT_END_TEXT = "End: --:--:--.---"

    # --- Public Signals ---
    set_start_clicked = pyqtSignal()
    set_end_clicked = pyqtSignal()
    cut_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Internal widgets, prefixed with _
        self._set_start_button: QPushButton
        self._start_label: QLabel
        self._set_end_button: QPushButton
        self._end_label: QLabel
        self._cut_button: QPushButton
        
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

        self._start_label = QLabel(self._DEFAULT_START_TEXT)
        self._start_label.setFixedWidth(120)
        self._end_label = QLabel(self._DEFAULT_END_TEXT)
        self._end_label.setFixedWidth(120)

    def _setup_layout(self):
        """Sets up the layout for the controls."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._set_start_button)
        layout.addWidget(self._start_label)
        layout.addWidget(self._set_end_button)
        layout.addWidget(self._end_label)
        layout.addStretch()
        layout.addWidget(self._cut_button)

    def _connect_signals(self):
        """Connects internal widget signals to the public signals of this class."""
        self._set_start_button.clicked.connect(self.set_start_clicked)
        self._set_end_button.clicked.connect(self.set_end_clicked)
        self._cut_button.clicked.connect(self.cut_clicked)

    def update_start_label(self, ms):
        self._start_label.setText(f"Start: {ms_to_time_str(ms)}")

    def update_end_label(self, ms):
        self._end_label.setText(f"End: {ms_to_time_str(ms)}")

    def reset_labels(self):
        self._start_label.setText(self._DEFAULT_START_TEXT)
        self._end_label.setText(self._DEFAULT_END_TEXT)
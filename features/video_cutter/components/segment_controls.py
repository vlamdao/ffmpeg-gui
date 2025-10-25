from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy)
from PyQt5.QtCore import QTime

class SegmentControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.set_start_button = QPushButton("Set Start")
        self.set_end_button = QPushButton("Set End")
        self.cut_button = QPushButton("Cut Segments")

        self.start_label = QLabel("Start: --:--:--.---")
        self.start_label.setFixedWidth(120)
        self.end_label = QLabel("End: --:--:--.---")
        self.end_label.setFixedWidth(120)

        layout.addWidget(self.set_start_button)
        layout.addWidget(self.start_label)
        layout.addWidget(self.set_end_button)
        layout.addWidget(self.end_label)
        layout.addStretch()
        layout.addWidget(self.cut_button)

    def _ms_to_time_str(self, ms):
        """Converts milliseconds to a HH:mm:ss.zzz string."""
        time = QTime(0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")

    def update_start_label(self, ms):
        self.start_label.setText(f"Start: {self._ms_to_time_str(ms)}")

    def update_end_label(self, ms):
        self.end_label.setText(f"End: {self._ms_to_time_str(ms)}")

    def reset_labels(self):
        self.start_label.setText("Start: --:--:--.---")
        self.end_label.setText("End: --:--:--.---")
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy)

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

    def reset_labels(self):
        self.start_label.setText("Start: --:--:--.---")
        self.end_label.setText("End: --:--:--.---")
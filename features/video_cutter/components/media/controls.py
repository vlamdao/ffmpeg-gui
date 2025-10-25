from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QStyle,
    QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtMultimedia import QMediaPlayer

from helper import ms_to_time_str
from .slider import MarkerSlider

class MediaControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.seek_backward_button = QPushButton()
        self.seek_backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setEnabled(False)

        self.seek_forward_button = QPushButton()
        self.seek_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))

        self.position_slider = MarkerSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setPageStep(1000)  # Jump 1 second
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 16px;
                background-color: #b5b5b5;
            }
            QSlider::handle:horizontal {
                background-color: blue; /* Match the painter's Qt.blue */
                width: 8px;
                height: 32px;
                margin: -8px 0; /* (32px - 16px) / 2 = 8px */
            }
        """)

        self.time_label = QLabel("00:00:00 / 00:00:00")

        layout.addWidget(self.seek_backward_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.seek_forward_button)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.time_label)

    def update_media_state(self, state):
        """Slot to update the play/pause button icon based on media player state."""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def update_position(self, position, duration):
        """Slot to update the slider and time label based on media player position."""
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        self.time_label.setText(f"{ms_to_time_str(position)} / {ms_to_time_str(duration)}")

    def update_duration(self, duration):
        """Slot to update the slider range and time label based on media duration."""
        self.position_slider.setRange(0, duration)
        # When duration changes, position is typically 0
        self.time_label.setText(f"{ms_to_time_str(0)} / {ms_to_time_str(duration)}")

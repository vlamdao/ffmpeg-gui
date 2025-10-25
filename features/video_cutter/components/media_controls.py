from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QStyle,
    QSizePolicy)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtMultimedia import QMediaPlayer

from .marker_slider import MarkerSlider

class MediaControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.previous_frame_button = QPushButton()
        self.previous_frame_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setEnabled(False)

        self.next_frame_button = QPushButton()
        self.next_frame_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))

        self.position_slider = MarkerSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setPageStep(1000)  # Jump 1 second
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 16px;
                background-color: #b5b5b5;
            }
            QSlider::handle:horizontal {
                background-color: #0078D7;
                width: 8px;
                height: 48px;
                margin: -3px 0;
            }
        """)

        self.time_label = QLabel("00:00:00 / 00:00:00")

        layout.addWidget(self.previous_frame_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.next_frame_button)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.time_label)

    def ms_to_time_str(self, ms):
        time = QTime(0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")

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
        self.time_label.setText(f"{self.ms_to_time_str(position)} / {self.ms_to_time_str(duration)}")

    def update_duration(self, duration, position):
        """Slot to update the slider range and time label based on media duration."""
        self.position_slider.setRange(0, duration)
        self.time_label.setText(f"{self.ms_to_time_str(position)} / {self.ms_to_time_str(duration)}")
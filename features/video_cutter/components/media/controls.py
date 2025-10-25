from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QStyle,
    QSizePolicy)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QSlider, QStyleOptionSlider
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt

from helper import ms_to_time_str

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

class MarkerSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.segment_markers = []
        self.current_start_marker = -1

    def set_segment_markers(self, segments):
        self.segment_markers = segments
        self.update()

    def set_current_start_marker(self, position):
        self.current_start_marker = position
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.maximum() == 0:
            return

        painter = QPainter(self)
        style = self.style()
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)

        # Draw existing segments
        pen = QPen(Qt.NoPen)
        brush = QBrush(Qt.blue, Qt.Dense4Pattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        for start_ms, end_ms in self.segment_markers:
            start_pos = int((start_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            end_pos = int((end_ms / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawRect(start_pos, groove_rect.y(), end_pos - start_pos, groove_rect.height())

        # Draw current start marker
        if self.current_start_marker != -1:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            marker_pos = int((self.current_start_marker / self.maximum()) * groove_rect.width()) + groove_rect.x()
            painter.drawLine(marker_pos, groove_rect.top(), marker_pos, groove_rect.bottom())
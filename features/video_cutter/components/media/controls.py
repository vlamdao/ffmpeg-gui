"""Module for media control widgets in the video cutter feature."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QStyle,
    QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtMultimedia import QMediaPlayer

from helper import ms_to_time_str
from .slider import MarkerSlider

class MediaControls(QWidget):
    """
    A widget providing media playback controls like play/pause, seek, and a
    position slider.
    """

    _SLIDER_STYLESHEET = """
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
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.seek_backward_button: QPushButton
        self.play_button: QPushButton
        self.seek_forward_button: QPushButton
        self.position_slider: MarkerSlider
        self.time_label: QLabel

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initializes and lays out the UI components."""
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self) -> None:
        """Creates the individual widgets for the control bar."""
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
        self.position_slider.setStyleSheet(self._SLIDER_STYLESHEET)

        self.time_label = QLabel("00:00:00 / 00:00:00")

    def _setup_layout(self) -> None:
        """Sets up the layout for the control bar."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.seek_backward_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.seek_forward_button)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.time_label)

    @pyqtSlot(QMediaPlayer.State)
    def update_media_state(self, state: QMediaPlayer.State) -> None:
        """Slot to update the play/pause button icon based on media player state."""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    @pyqtSlot(int, int)
    def update_position(self, position: int, duration: int) -> None:
        """Slot to update the slider and time label based on media player position."""
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)

        if duration > 0:
            self.time_label.setText(f"{ms_to_time_str(position)} / {ms_to_time_str(duration)}")

    @pyqtSlot(int)
    def update_duration(self, duration: int) -> None:
        """Slot to update the slider range and time label based on media duration."""
        self.position_slider.setRange(0, duration)
        # When duration changes, position is typically 0
        self.time_label.setText(f"{ms_to_time_str(0)} / {ms_to_time_str(duration)}")
        self.play_button.setEnabled(duration > 0)

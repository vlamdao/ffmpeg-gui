from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QStyle,
    QSizePolicy, QSlider)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer

from helper import ms_to_time_str
from .slider import SeekSlider

class MediaControls(QWidget):
    """A widget providing media playback controls like play/pause, seek, and a position slider.

    This class encapsulates all the interactive elements for controlling the media
    player. It communicates user actions to the parent widget via signals, allowing
    for a decoupled architecture.
    """
    # Stylesheet for the custom slider to ensure a consistent look.
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
    # --- Public Signals ---
    play_clicked = pyqtSignal()
    """Emitted when the play/pause button is clicked."""
    seek_forward_clicked = pyqtSignal()
    """Emitted when the seek forward button is clicked."""
    seek_backward_clicked = pyqtSignal()
    """Emitted when the seek backward button is clicked."""
    slider_pressed = pyqtSignal()
    """Emitted when the user presses the mouse on the slider."""
    position_changed = pyqtSignal(int)
    """Emitted when the slider's value is changed by the user."""

    def __init__(self, parent: QWidget | None = None, slider_class: type[QSlider] = SeekSlider) -> None:
        """Initializes the MediaControls widget."""
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._slider_class = slider_class

        # Internal widgets, prefixed with _
        self._seek_backward_button: QPushButton
        self._play_button: QPushButton
        self._seek_forward_button: QPushButton
        self._position_slider: QSlider
        self._time_label: QLabel
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Initializes and lays out the UI components."""
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self) -> None:
        """Creates the individual widgets for the control bar."""
        self._seek_backward_button = QPushButton()
        self._seek_backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))

        self._play_button = QPushButton()
        self._play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self._play_button.setEnabled(False)

        self._seek_forward_button = QPushButton()
        self._seek_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))

        self._position_slider = self._slider_class(Qt.Horizontal)
        self._position_slider.setRange(0, 0)
        self._position_slider.setPageStep(1000)  # Jump 1 second
        self._position_slider.setStyleSheet(self._SLIDER_STYLESHEET)

        self._time_label = QLabel("00:00:00 / 00:00:00")

    def _setup_layout(self) -> None:
        """Sets up the layout for the control bar."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._seek_backward_button)
        layout.addWidget(self._play_button)
        layout.addWidget(self._seek_forward_button)
        layout.addWidget(self._position_slider)
        layout.addWidget(self._time_label)

    def _connect_signals(self) -> None:
        """Connects internal widgets to the public signals of this class."""
        self._play_button.clicked.connect(self.play_clicked)
        self._seek_backward_button.clicked.connect(self.seek_backward_clicked)
        self._seek_forward_button.clicked.connect(self.seek_forward_clicked)
        self._position_slider.sliderPressed.connect(self.slider_pressed)
        self._position_slider.valueChanged.connect(self.position_changed)

    @pyqtSlot(QMediaPlayer.State)
    def update_media_state(self, state: QMediaPlayer.State) -> None:
        """Slot to update the play/pause button icon based on media player state."""
        if state == QMediaPlayer.PlayingState:
            self._play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self._play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    @pyqtSlot(int, int)
    def update_position(self, position: int, duration: int) -> None:
        """Slot to update the slider and time label based on media player position."""
        self._position_slider.blockSignals(True)
        self._position_slider.setValue(position)
        self._position_slider.blockSignals(False)

        if duration > 0:
            self._time_label.setText(f"{ms_to_time_str(position)} / {ms_to_time_str(duration)}")

    @pyqtSlot('qint64')
    def update_duration(self, duration: int) -> None:
        """Slot to update the slider range and time label based on media duration."""
        self._position_slider.setRange(0, duration)
        # When duration changes, position is typically 0
        self._time_label.setText(f"{ms_to_time_str(0)} / {ms_to_time_str(duration)}")
        self._play_button.setEnabled(duration > 0)

    @pyqtSlot(list)
    def set_segment_markers(self, segments: list) -> None:
        """Slot to pass segment data to the underlying slider for painting."""
        self._position_slider.set_segment_markers(segments)

    @pyqtSlot(int)
    def set_current_start_marker(self, position: int) -> None:
        """Slot to pass the current start marker position to the slider for painting."""
        self._position_slider.set_current_start_marker(position)

    def set_play_button_enabled(self, enabled: bool) -> None:
        """Public method to control the enabled state of the play button."""
        self._play_button.setEnabled(enabled)

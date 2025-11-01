import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QUrl, pyqtSignal, Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class MediaPlayer(QWidget):
    """A widget that encapsulates QMediaPlayer and QVideoWidget."""

    # Signals to communicate with the parent widget
    media_loaded = pyqtSignal(bool)
    position_changed = pyqtSignal('qint64')
    duration_changed = pyqtSignal('qint64')
    state_changed = pyqtSignal(QMediaPlayer.State)
    double_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initializes the MediaPlayer widget."""
        super().__init__(parent)
        # A small buffer to correctly detect when media has reached its end.
        self._END_OF_MEDIA_THRESHOLD_MS = 100  # Threshold to consider media as "finished"
        self._is_media_loaded = False
        self._seek_interval_ms = 1000  # Seek interval: 1 second
        self._media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self._video_widget = ClickableVideoWidget()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._video_widget.setMinimumHeight(200) # Set a reasonable minimum height
        layout.addWidget(self._video_widget, 1) # Give it expanding space
        self._media_player.setVideoOutput(self._video_widget)

    def _connect_signals(self):
        self._media_player.positionChanged.connect(self.position_changed)
        self._media_player.durationChanged.connect(self.duration_changed)
        self._media_player.stateChanged.connect(self.state_changed)
        self._video_widget.doubleClicked.connect(self.double_clicked)

    def load_media(self, video_path):
        """Loads the media from the given path."""
        if self._is_media_loaded:
            return

        if os.path.exists(video_path):
            self._media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
            self._is_media_loaded = True
            self.media_loaded.emit(True)
            self.play()
        else:
            QMessageBox.critical(self, "Error", f"Video file not found:\n{video_path}")
            self.media_loaded.emit(False)

    def stop(self):
        """Stops the media player and resets its position."""
        self._media_player.stop()

    def play(self):
        """Starts or resumes playback."""
        self._media_player.play()

    def pause(self):
        """Pauses playback."""
        self._media_player.pause()

    def toggle_play(self):
        """Toggles play/pause state. Restarts if at the end."""
        # If the video is at the end, restart from the beginning.
        if self.duration() > 0 and self.position() >= self.duration() - self._END_OF_MEDIA_THRESHOLD_MS:
            self.set_position(0)
            self.play()
        elif self.state() == QMediaPlayer.PlayingState:
            # If playing, pause.
            self.pause()
        else:
            self.play()

    def seek_forward(self):
        self.pause()
        new_position = self.position() + self._seek_interval_ms
        self.set_position(int(new_position))

    def seek_backward(self):
        self.pause()
        new_position = self.position() - self._seek_interval_ms
        self.set_position(int(max(0, new_position)))

    def set_position(self, position):
        """Sets the media player's position if it's different from the current one."""
        if self._media_player.isSeekable() and self._media_player.position() != position:
            self._media_player.setPosition(position)

    def position(self):
        """Returns the current playback position in milliseconds."""
        return self._media_player.position()

    def duration(self):
        """Returns the total duration of the media in milliseconds."""
        return self._media_player.duration()

    def state(self):
        """Returns the current state of the media player (e.g., PlayingState)."""
        return self._media_player.state()
    
class ClickableVideoWidget(QVideoWidget):
    """A QVideoWidget that emits a doubleClicked signal on a left-button double-click."""
    doubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initializes the ClickableVideoWidget."""
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event):
        """Emits the doubleClicked signal if the event was from the left mouse button."""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


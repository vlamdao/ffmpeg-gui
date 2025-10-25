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
        super().__init__(parent)
        self._is_media_loaded = False
        self.seek_interval_ms = 500  # Seek interval: 0.5 seconds
        self._pause_after_seek_pending = False # Flag to indicate if we need to pause after a seek
        self._media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self._video_widget = ClickableVideoWidget()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._video_widget.setMinimumHeight(300)
        layout.addWidget(self._video_widget, 1) # Give it expanding space
        self._media_player.setVideoOutput(self._video_widget)

    def _connect_signals(self):
        self._media_player.positionChanged.connect(self._on_media_player_position_changed) # Internal handler for seek logic
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
        self._media_player.stop()

    def play(self):
        self._media_player.play()

    def pause(self):
        self._media_player.pause()

    def toggle_play(self):
        """Toggles play/pause state. Restarts if at the end."""
        if self.position() >= self.duration() - 100:
            self.set_position(0)
            self.play()
        elif self.state() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()

    def seek_forward(self):
        self.pause()
        new_position = self.position() + self.seek_interval_ms
        self.set_position(int(new_position))

    def seek_backward(self):
        self.pause()
        new_position = self.position() - self.seek_interval_ms
        self.set_position(int(max(0, new_position)))

    def set_position(self, position):
        """
        Sets the media player's position.

        This method handles seeking more robustly. It seeks to the desired
        position and then pauses the video again after the seek is complete
        to ensure the video frame is stable at the new position. This helps
        mitigate issues where playback might start from a nearby keyframe.
        """
        if self._media_player.isSeekable() and self._media_player.position() != position:
            self._pause_after_seek_pending = True # Set flag before seeking
            self._media_player.setPosition(position)

    def _on_media_player_position_changed(self, position):
        """
        Internal slot to handle position changes, specifically for pausing after a seek.
        This helps to "lock" the video frame after a seek operation.
        """
        # Only pause if a seek operation was initiated and we are waiting to pause
        if self._pause_after_seek_pending:
            # It's good practice to check if the player is still seeking or has settled
            # For now, we'll pause immediately.
            self._media_player.pause()
            self._pause_after_seek_pending = False # Reset the flag

    def position(self):
        return self._media_player.position()

    def duration(self):
        return self._media_player.duration()

    def state(self):
        return self._media_player.state()
    
class ClickableVideoWidget(QVideoWidget):
    """A QVideoWidget that emits a doubleClicked signal."""
    doubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
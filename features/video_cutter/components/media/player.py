import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QUrl, pyqtSignal
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
        self.frame_step_ms = 33  # ~30fps
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

    def next_frame(self):
        self.pause()
        new_position = self.position() + self.frame_step_ms
        self.set_position(int(new_position))

    def previous_frame(self):
        self.pause()
        new_position = self.position() - self.frame_step_ms
        self.set_position(int(max(0, new_position)))

    def set_position(self, position):
        if self._media_player.position() != position:
            self._media_player.setPosition(position)

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
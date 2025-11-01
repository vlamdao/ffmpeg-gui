import os
import tempfile
import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication
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
        self._temp_cfr_video_path = None
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

    def _create_cfr_copy(self, video_path: str) -> str | None:
        """
        Creates a temporary copy of the video with a constant frame rate (CFR)
        to prevent sync issues with VFR videos in QMediaPlayer.
        """
        try:
            # Create a temporary file with the same extension
            _, extension = os.path.splitext(video_path)
            fd, temp_path = tempfile.mkstemp(suffix=extension)
            os.close(fd)

            # Use FFmpeg to create a CFR copy without re-encoding (fast)
            command = [
                'ffmpeg', '-y', '-i', video_path,
                '-vsync', 'cfr', '-c:v', 'copy', '-c:a', 'copy',
                temp_path
            ]
            
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Show a "please wait" cursor
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            process = subprocess.run(command, check=True, capture_output=True, text=True, startupinfo=startupinfo)
            
            QApplication.restoreOverrideCursor()
            return temp_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            QApplication.restoreOverrideCursor()
            error_message = f"Failed to create CFR copy for playback: {e}"
            if isinstance(e, subprocess.CalledProcessError):
                error_message += f"\nFFmpeg stderr:\n{e.stderr}"
            QMessageBox.warning(self, "Playback Warning", error_message)
            return None

    def load_media(self, video_path):
        """Loads the media from the given path."""
        self.cleanup() # Clean up any previous temp file

        if os.path.exists(video_path):
            # Create a CFR copy to handle VFR videos correctly
            self._temp_cfr_video_path = self._create_cfr_copy(video_path)
            
            # Play the temp file if created, otherwise fall back to original
            path_to_play = self._temp_cfr_video_path if self._temp_cfr_video_path else video_path
            
            self._media_player.setMedia(QMediaContent(QUrl.fromLocalFile(path_to_play)))
            self._is_media_loaded = True
            self.media_loaded.emit(True)
            self.play()
        else:
            QMessageBox.critical(self, "Error", f"Video file not found:\n{video_path}")
            self.media_loaded.emit(False)

    def cleanup(self):
        """Cleans up temporary files."""
        self.stop()
        self._media_player.setMedia(QMediaContent()) # Release the file lock
        if self._temp_cfr_video_path and os.path.exists(self._temp_cfr_video_path):
            try:
                os.remove(self._temp_cfr_video_path)
            except OSError as e:
                print(f"Error removing temp file: {e}") # Or log this
        self._temp_cfr_video_path = None
        self._is_media_loaded = False

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
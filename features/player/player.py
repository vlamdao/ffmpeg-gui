import os
import sys
import vlc
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer as QtMediaPlayerState # For state enum

class MediaPlayer(QWidget):
    """
    A media player widget using python-vlc for robust playback.
    This class is designed as a drop-in replacement for the QMediaPlayer-based player,
    providing the same public API (signals and methods).
    """

    # Signals mimicking QMediaPlayer for compatibility
    media_loaded = pyqtSignal(bool)
    position_changed = pyqtSignal('qint64')
    duration_changed = pyqtSignal('qint64')
    state_changed = pyqtSignal(QtMediaPlayerState.State)
    double_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initializes the VlcMediaPlayer widget."""
        super().__init__(parent)

        # --- VLC Setup ---
        vlc_options = [
            "--no-xlib",  # Prevent VLC from creating its own X window on Linux
            "--no-video-title-show", # Don't show the video title
            "--no-stats", # Disable statistics gathering
            "--avcodec-hw=any", # Try to use hardware decoding
            "--file-caching=300" # Set file caching to 300ms
        ]
        self._vlc_instance = vlc.Instance(" ".join(vlc_options))
        self._media_player = self._vlc_instance.media_player_new()

        # --- UI Setup ---
        self._video_frame = QFrame()
        self._video_frame.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._video_frame)

        # Set the window handle for VLC to draw on
        if sys.platform.startswith('linux'):
            self._media_player.set_xwindow(self._video_frame.winId())
        elif sys.platform == 'win32':
            self._media_player.set_hwnd(self._video_frame.winId())
        elif sys.platform == 'darwin':
            self._media_player.set_nsobject(int(self._video_frame.winId()))

        # --- State Management ---
        self._is_media_loaded = False
        self._current_state = QtMediaPlayerState.StoppedState
        self._is_cleaned_up = False
        self._seek_interval_ms = 1000

        # --- VLC Event Handling ---
        # Connect to VLC's event manager to emit Qt signals.
        self._event_manager = self._media_player.event_manager()
        self._connect_vlc_events()

    def _connect_vlc_events(self):
        """Connects to VLC's internal event system to emit Qt signals."""
        self._event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_vlc_state_change)
        self._event_manager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_vlc_state_change)
        self._event_manager.event_attach(vlc.EventType.MediaPlayerStopped, self._on_vlc_state_change)
        self._event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_vlc_state_change)
        self._event_manager.event_attach(vlc.EventType.MediaPlayerPositionChanged, self._on_vlc_position_change)
        self._event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self._on_vlc_duration_change)

    def _on_vlc_position_change(self, event):
        """Handles position changes from VLC and emits a Qt signal."""
        self.position_changed.emit(self.position())

    def _on_vlc_state_change(self, event):
        """Handles state changes from VLC and maps them to Qt states."""
        new_state = self._media_player.get_state()
        qt_state = QtMediaPlayerState.StoppedState

        if new_state in (vlc.State.Playing, vlc.State.Opening):
            qt_state = QtMediaPlayerState.PlayingState
        elif new_state == vlc.State.Paused:
            qt_state = QtMediaPlayerState.PausedState
        # For Stopped, Ended, Error
        else:
            qt_state = QtMediaPlayerState.StoppedState

        if self._current_state != qt_state:
            self._current_state = qt_state
            self.state_changed.emit(self._current_state)

    def _on_vlc_duration_change(self, event):
        """Handles duration changes from VLC."""
        # event.u.new_length is the new length in ms
        self.duration_changed.emit(self.duration())

    def load_media(self, video_path: str):
        """Loads media from a file path."""
        # Stop any currently playing media before loading a new one.
        if self._media_player.is_playing():
            self.stop()

        if not os.path.exists(video_path):
            QMessageBox.critical(self, "Error", f"Video file not found:\n{video_path}")
            self.media_loaded.emit(False)
            return

        media = self._vlc_instance.media_new(video_path)
        self._media_player.set_media(media)
        self._is_media_loaded = True
        self.media_loaded.emit(True)
        self.play()

    def cleanup(self):
        """Stops playback and releases VLC resources."""
        if self._is_cleaned_up:
            return

        self.stop_and_release_player()
        self._vlc_instance.release()
        self._is_cleaned_up = True

    def stop_and_release_player(self):
        """Stops playback and releases the media player object, but not the VLC instance."""
        if self._media_player is not None:
            self.stop()
            self._media_player.release()
            self._media_player = None
        self._is_media_loaded = False

    def stop(self):
        """Stops the media player."""
        if self._media_player:
            self._media_player.stop()

    def play(self):
        """Starts or resumes playback."""
        if self._media_player and self._is_media_loaded:
            self._media_player.play()

    def pause(self):
        """Pauses playback."""
        if self._media_player:
            self._media_player.pause() # This is a toggle in VLC

    def toggle_play(self):
        """Toggles play/pause state."""
        if self.state() == QtMediaPlayerState.PlayingState:
            self.pause()
        else:
            self.play()

    def seek_forward(self):
        """Seeks forward by a fixed interval."""
        new_pos = self.position() + self._seek_interval_ms
        self.set_position(new_pos)

    def seek_backward(self):
        """Seeks backward by a fixed interval."""
        new_pos = self.position() - self._seek_interval_ms
        self.set_position(max(0, new_pos))

    def set_position(self, position_ms: int):
        """Sets the media player's position in milliseconds."""
        if self._media_player.is_seekable():
            self._media_player.set_time(position_ms)
            # Manually emit signal after seeking
            self.position_changed.emit(position_ms)

    def position(self) -> int:
        """Returns the current playback position in milliseconds."""
        return self._media_player.get_time()

    def duration(self) -> int:
        """Returns the total duration of the media in milliseconds."""
        return self._media_player.get_length()

    def state(self) -> QtMediaPlayerState.State:
        """Returns the current state of the media player."""
        return self._current_state

    def closeEvent(self, event):
        """Ensures resources are cleaned up when the widget is closed."""
        self.cleanup()
        super().closeEvent(event)

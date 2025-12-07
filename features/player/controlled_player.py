from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSlider)
from PyQt5.QtCore import pyqtSlot
from features.player import MediaPlayer, MediaControls

class ControlledPlayer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._media_player = MediaPlayer()
        self._media_controls = MediaControls()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self._media_player, 1)
        main_layout.addWidget(self._media_controls)
    
    def _connect_signals(self):
        self._media_controls.play_clicked.connect(self._media_player.toggle_play)
        self._media_controls.seek_backward_clicked.connect(self._media_player.seek_backward)
        self._media_controls.seek_forward_clicked.connect(self._media_player.seek_forward)
        self._media_controls.seek_requested.connect(self._media_player.set_position)

        self._media_player.media_loaded.connect(self._media_controls.set_play_button_enabled)
        self._media_player.state_changed.connect(self._media_controls.update_media_state)
        self._media_player.position_changed.connect(
            lambda position: self._media_controls.update_position(position, self.duration())
        )
        self._media_player.duration_changed.connect(self._media_controls.update_duration)

    # ========================================
    # Widget Access
    # ========================================
    def get_video_widget(self) -> QWidget:
        """Returns the widget where the video is rendered."""
        return self._media_player.get_video_widget()


    # ========================================
    # Load and cleanup
    # ========================================
    def load_media(self, media_path):
        """Loads media into the player."""
        self._media_player.load_media(media_path)

    def cleanup(self):
        """Cleans up the player."""
        self._media_player.cleanup()

    # ========================================
    # Player function
    # ========================================
    def pause(self):
        """Pauses the player."""
        self._media_player.pause()

    def play(self):
        """Plays the media."""
        self._media_player.play()

    def stop(self):
        """Stops the media."""
        self._media_player.stop()

    # ========================================
    # Getters and setters
    # ========================================
    def position(self):
        """Returns the current position of the player."""
        return self._media_player.position()

    def duration(self):
        """Returns the duration of the media."""
        return self._media_player.duration()

    def state(self):
        """Returns the current state of the player."""
        return self._media_player.state()
    
    def get_video_resolution(self) -> tuple[int, int]:
        """Returns the resolution (width, height) of the loaded video."""
        return self._media_player.get_video_resolution()

    def set_position(self, position):
        """Sets the position of the player."""
        self._media_player.set_position(position)
        
    # ========================================
    # Controls function
    # ========================================
    def set_segment_markers(self, segments: list):
        """Sets the segment markers for the player."""
        self._media_controls.set_segment_markers(segments)

    def set_current_start_marker(self, position: int):
        """Sets the current start marker for the player."""
        self._media_controls.set_current_start_marker(position)
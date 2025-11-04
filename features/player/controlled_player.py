from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QLabel, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize

from features.player import MediaPlayer, MediaControls
from components import PlaceholdersTable
from helper import ms_to_time_str, time_str_to_ms, resource_path

class ControlledPlayer(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._media_player: MediaPlayer
        self._media_controls: MediaControls

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self._media_player = MediaPlayer()
        self._media_controls = MediaControls()

        main_layout.addWidget(self._media_player, 1)
        main_layout.addWidget(self._media_controls)
    
    def _connect_signals(self):
        """Connects signals and slots for the dialog's components."""
        # --- Media Player and Controls ---
        self._media_controls.play_clicked.connect(self._media_player.toggle_play)
        self._media_controls.seek_backward_clicked.connect(self._media_player.seek_backward)
        self._media_controls.seek_forward_clicked.connect(self._media_player.seek_forward)
        self._media_controls.seek_requested.connect(self._media_player.set_position)

        self._media_player.media_loaded.connect(self._media_controls.set_play_button_enabled)
        self._media_player.state_changed.connect(self._media_controls.update_media_state)
        self._media_player.position_changed.connect(self._on_position_changed)
        self._media_player.duration_changed.connect(self._media_controls.update_duration)
        # self._media_player.double_clicked.connect(self._media_player.toggle_play)

    @pyqtSlot('qint64')
    def _on_position_changed(self, position):
        """Updates the media controls when the player's position changes."""
        self._media_controls.update_position(position, self._media_player.duration())

    def load_media(self, media_path):
        """Loads media into the player."""
        self._media_player.load_media(media_path)

    def cleanup(self):
        """Cleans up the player."""
        self._media_player.cleanup()

    def position(self):
        """Returns the current position of the player."""
        return self._media_player.position()

    def duration(self):
        """Returns the duration of the media."""
        return self._media_player.duration()

    def state(self):
        """Returns the current state of the player."""
        return self._media_player.state()
    
    def set_position(self, position):
        """Sets the position of the player."""
        self._media_player.set_position(position)
        
    def pause(self):
        """Pauses the player."""
        self._media_player.pause()

    
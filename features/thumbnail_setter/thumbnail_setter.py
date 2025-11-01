import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QLabel, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize

from features.player import MediaPlayer, MediaControls
from .processor import ThumbnailProcessor
from helper import ms_to_time_str, time_str_to_ms, resource_path
from components import Logger

class ThumbnailSetter(QDialog):
    """
    A dialog for selecting a frame from a video to be used as a thumbnail.
    """

    def __init__(self, video_path: str, output_path: str, logger: Logger, parent=None):
        """
        Initializes the ThumbnailSetter dialog.

        Args:
            video_path (str): The absolute path to the video file.
            output_path (str): The path to the output directory.
            logger (Logger): An instance of the logger for displaying messages.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Set Thumbnail")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(950, 650)
        self.setModal(False) # Allow interaction with main window

        # Dependencies
        self._video_path = video_path
        self._logger = logger
        self._output_path = output_path

        # UI Components
        self._media_player: MediaPlayer
        self._media_controls: MediaControls
        self._timestamp_edit: QLineEdit
        self._go_to_button: QPushButton
        self._set_thumbnail_button: QPushButton

        # Thumbnail Processor
        self._processor = ThumbnailProcessor(self)

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self._media_player.load_media(self._video_path)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player."""
        self._media_player.cleanup()
        super().closeEvent(event)

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Player and Controls ---
        self._media_player = MediaPlayer()
        self._media_controls = MediaControls()

        # --- Thumbnail Controls ---
        thumbnail_controls_widget = QWidget()
        thumbnail_controls_layout = QHBoxLayout(thumbnail_controls_widget)
        thumbnail_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        min_height = 32
        self._timestamp_edit = QLineEdit()
        self._timestamp_edit.setInputMask("00:00:00.000")
        self._timestamp_edit.setText("00:00:00.000")
        self._timestamp_edit.setFixedWidth(120)
        self._timestamp_edit.setMinimumHeight(min_height)
        self._timestamp_edit.setFont(QFont("Consolas", 9))
        self._timestamp_edit.setAlignment(Qt.AlignCenter)
        
        self._go_to_button = QPushButton("Go ")
        self._go_to_button.setIcon(QIcon(resource_path("icon/go.png")))
        self._go_to_button.setIconSize(QSize(20, 20))
        self._go_to_button.setLayoutDirection(Qt.RightToLeft)
        self._go_to_button.setMinimumHeight(min_height)
        self._go_to_button.setToolTip("Seek to the entered timestamp")

        self._set_thumbnail_button = QPushButton(" Set Thumbnail")
        self._set_thumbnail_button.setIcon(QIcon(resource_path("icon/run-set-thumbnail.png")))
        self._set_thumbnail_button.setIconSize(QSize(20, 20))
        self._set_thumbnail_button.setStyleSheet("padding-left: 12px; padding-right: 12px;")
        self._set_thumbnail_button.setMinimumHeight(min_height)
        self._set_thumbnail_button.setToolTip("Set the thumbnail at the current frame")

        thumbnail_controls_layout.addStretch()
        thumbnail_controls_layout.addWidget(self._timestamp_edit)
        thumbnail_controls_layout.addWidget(self._go_to_button)
        thumbnail_controls_layout.addWidget(self._set_thumbnail_button)

        # --- Assemble Layout ---
        main_layout.addWidget(self._media_player, 1) # Player takes expanding space
        main_layout.addWidget(self._media_controls)
        main_layout.addWidget(thumbnail_controls_widget)

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
        self._media_player.double_clicked.connect(self._media_player.toggle_play)

        # --- Custom Controls ---
        self._go_to_button.clicked.connect(self._on_go_to_timestamp)
        self._set_thumbnail_button.clicked.connect(self._on_set_thumbnail)
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)

    @pyqtSlot('qint64')
    def _on_position_changed(self, position):
        """Updates the media controls when the player's position changes."""
        self._media_controls.update_position(position, self._media_player.duration())

    @pyqtSlot()
    def _on_go_to_timestamp(self):
        """When the user clicks 'Go', seek the player to the manually entered time."""
        time_str = self._timestamp_edit.text()
        try:
            pos_ms = time_str_to_ms(time_str)
            if not (0 <= pos_ms <= self._media_player.duration()):
                raise ValueError("Time is out of video duration range.")
            self._media_player.set_position(pos_ms)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Time", f"Invalid timestamp format or value: {time_str}\n{e}")

    @pyqtSlot()
    def _on_set_thumbnail(self):
        """
        Generates and executes FFmpeg commands to extract a thumbnail image
        and then embed it into the video file.
        """
        if self._processor.is_running():
            QMessageBox.warning(self, "In Progress", "A thumbnail operation is already in progress.")
            return
        
        # Always use the current player position for setting the thumbnail
        timestamp = ms_to_time_str(self._media_player.position())
        
        # Disable button and pause video when processing
        self._set_thumbnail_button.setEnabled(False)
        self._go_to_button.setEnabled(False)
        self._timestamp_edit.setEnabled(False)
        self._media_player.pause()
        
        self._processor.start(self._video_path, self._output_path, timestamp)

    @pyqtSlot(bool, str)
    def _on_processing_finished(self, success: bool, message: str):
        """Handles the completion of the thumbnail process."""
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
        self._set_thumbnail_button.setEnabled(True)
        self._go_to_button.setEnabled(True)
        self._timestamp_edit.setEnabled(True)


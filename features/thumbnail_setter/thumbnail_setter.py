import os
import tempfile
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QLabel, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot

from features.player import MediaPlayer, MediaControls
from processor import FFmpegWorker
from helper import ms_to_time_str, time_str_to_ms

class ThumbnailSetter(QDialog):
    """
    A dialog for selecting a frame from a video to be used as a thumbnail.
    """

    def __init__(self, video_path: str, output_path: str, logger, parent=None):
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
        self.setMinimumSize(800, 600)
        self.setModal(False) # Allow interaction with main window

        # Dependencies
        self._video_path = video_path
        self._logger = logger

        # UI Components
        self._media_player: MediaPlayer
        self._media_controls: MediaControls
        self._timestamp_edit: QLineEdit
        self._set_thumbnail_button: QPushButton

        # FFmpeg worker
        self._worker: FFmpegWorker | None = None
        self._output_path = output_path

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self._media_player.load_media(self._video_path)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player."""
        self._media_player.stop()
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
        
        timestamp_label = QLabel("Timestamp:")
        self._timestamp_edit = QLineEdit()
        self._timestamp_edit.setPlaceholderText("00:00:00.000")
        self._timestamp_edit.setFixedWidth(120)
        self._set_thumbnail_button = QPushButton("Set Thumbnail")

        thumbnail_controls_layout.addStretch()
        thumbnail_controls_layout.addWidget(timestamp_label)
        thumbnail_controls_layout.addWidget(self._timestamp_edit)
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
        self._media_controls.slider_pressed.connect(self._media_player.pause)
        self._media_controls.position_changed.connect(self._media_player.set_position)

        self._media_player.media_loaded.connect(self._media_controls.set_play_button_enabled)
        self._media_player.state_changed.connect(self._media_controls.update_media_state)
        self._media_player.position_changed.connect(self._on_position_changed)
        self._media_player.duration_changed.connect(self._media_controls.update_duration)
        self._media_player.double_clicked.connect(self._media_player.toggle_play)

        # --- Thumbnail Controls ---
        self._media_player.position_changed.connect(self._update_timestamp_display)
        self._timestamp_edit.editingFinished.connect(self._on_timestamp_edited)
        self._set_thumbnail_button.clicked.connect(self._on_set_thumbnail)

    @pyqtSlot('qint64')
    def _on_position_changed(self, position):
        """Updates the media controls when the player's position changes."""
        self._media_controls.update_position(position, self._media_player.duration())
    
    @pyqtSlot()
    def _update_timestamp_display(self):
        """Updates the timestamp QLineEdit with the current player position."""
        # Only update if the user is not currently editing it
        if not self._timestamp_edit.hasFocus():
            self._timestamp_edit.setText(ms_to_time_str(self._media_player.position()))

    @pyqtSlot()
    def _on_timestamp_edited(self):
        """When the user manually edits the timestamp, seek the player to that time."""
        time_str = self._timestamp_edit.text()
        try:
            pos_ms = time_str_to_ms(time_str)
            if 0 <= pos_ms <= self._media_player.duration():
                self._media_player.set_position(pos_ms)
            else:
                raise ValueError("Time is out of video duration range.")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Time", f"Invalid timestamp format or value: {time_str}\n{e}")
            # Revert to current player time
            self._timestamp_edit.setText(ms_to_time_str(self._media_player.position()))

    @pyqtSlot()
    def _on_set_thumbnail(self):
        """
        Generates and executes FFmpeg commands to extract a thumbnail image
        and then embed it into the video file.
        """
        timestamp = self._timestamp_edit.text()
        if not timestamp:
            QMessageBox.warning(self, "No Frame Selected", "Please select a frame first.")
            return
        
        self._set_thumbnail_button.setEnabled(False)
        self._media_player.pause()

        input_folder = os.path.dirname(self._video_path)
        filename, ext = os.path.splitext(os.path.basename(self._video_path))
        ext = ext.lstrip('.')

        # Create a temporary file for the thumbnail image
        thumb_fd, thumb_path = tempfile.mkstemp(suffix=".jpg", prefix=f"{filename}_thumb_")
        os.close(thumb_fd) # Close the file handle

        # Command 1: Extract the thumbnail image
        cmd1 = (f'ffmpeg -ss {timestamp} -i "{self._video_path}" '
                f'-frames:v 1 -y "{thumb_path}"')

        # Command 2: Embed the thumbnail
        # Create a temporary output file to avoid read/write conflicts on the same file
        output_fd, output_path = tempfile.mkstemp(suffix=f".{ext}", prefix=f"{filename}_thumbed_")
        os.close(output_fd)

        # cmd2 = (f'ffmpeg -i "{self._video_path}" -i "{thumb_path}" '
        #         f'-map 0 -map 1 -c copy -disposition:v:1 attached_pic -y "{output_path}"')
        
        self._logger.append_log(f"Thumbnail to be set at: {timestamp} for video: {self._video_path}")
        QMessageBox.information(self, "Set Thumbnail", f"Logic to set thumbnail at {timestamp} goes here.")
        # Here you would typically start an FFmpeg worker
        self.accept()
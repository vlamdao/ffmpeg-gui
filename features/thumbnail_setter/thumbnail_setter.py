import os
import tempfile
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QLabel, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize

from features.player import MediaPlayer, MediaControls
from processor import FFmpegWorker
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

        # FFmpeg worker
        self._worker: FFmpegWorker | None = None

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
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "In Progress", "A thumbnail operation is already in progress.")
            return
        
        # Always use the current player position for setting the thumbnail
        timestamp = ms_to_time_str(self._media_player.position())
        
        # disable button and pause video when processing
        self._set_thumbnail_button.setEnabled(False)
        self._media_player.pause()
        
        try:
            commands, temp_thumb_path = self._create_commands(timestamp)
            self._start_thumbnail_worker(commands, temp_thumb_path)
            self._logger.append_log(f"Setting thumbnail for '{os.path.basename(self._video_path)}' at {timestamp}...")
        except Exception as e:
            self._logger.append_log(f"Error preparing thumbnail job: {e}")
            QMessageBox.critical(self, "Error", f"Could not start thumbnail process: {e}")
            self._set_thumbnail_button.setEnabled(True)

    def _create_commands(self, timestamp: str) -> tuple[list[str], str]:
        """
        Creates the FFmpeg commands for extracting and embedding a thumbnail.
        
        Args:
            timestamp (str): The timestamp for the thumbnail (e.g., "00:01:23.456").
            
        Returns:
            A tuple containing the list of commands and the path to the temporary thumbnail file.
        """
        filename = os.path.basename(self._video_path)
        # Create a temporary file for the thumbnail image
        thumb_fd, thumb_path = tempfile.mkstemp(suffix=".jpg", prefix=f"{filename}_thumb_")
        os.close(thumb_fd)

        # Ensure output directory exists
        os.makedirs(self._output_path, exist_ok=True)
        output_file_path = os.path.join(self._output_path, filename)

        cmd1 = (f'ffmpeg -y -loglevel warning -ss {timestamp} -i "{self._video_path}" '
                f'-frames:v 1 "{thumb_path}"')

        cmd2 = (f'ffmpeg -y -loglevel warning -i "{self._video_path}" -i "{thumb_path}" '
                f'-map 0 -map 1 -c copy -disposition:v:1 attached_pic "{output_file_path}"')
        
        return [cmd1, cmd2], thumb_path

    def _start_thumbnail_worker(self, commands: list[str], temp_thumb_path: str):
        """Initializes and starts the FFmpegWorker for the thumbnail job."""
        job = (-1, commands) # Use -1 for row_index as this is a single job
        self._worker = FFmpegWorker([job])
        self._worker.log_signal.connect(self._logger.append_log)
        self._worker.update_status.connect(self._on_worker_status_update)
        self._worker.finished.connect(lambda: self._on_worker_thread_finished(temp_thumb_path))
        self._worker.start()

    @pyqtSlot(int, str)
    def _on_worker_status_update(self, row_index: int, status: str):
        """Slot to handle status updates from the worker."""
        # We only care about the final status, not "Processing"
        if status in ["Success", "Failed", "Stopped"]:
            if status == "Success":
                QMessageBox.information(self, "Success", "Thumbnail has been set successfully.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to set thumbnail. Status: {status}")
            self._set_thumbnail_button.setEnabled(True)

    def _on_worker_thread_finished(self, temp_thumb_path: str):
        """Slot called when the FFmpeg worker thread has finished."""
        # Clean up the temporary thumbnail file
        if os.path.exists(temp_thumb_path):
            os.remove(temp_thumb_path)
        self._worker = None

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon

from features.player import ControlledPlayer
from .processor import ThumbnailProcessor
from .components import (CommandTemplates, ThumbnailPlaceholders,
                         ActionPanel
                         )
from components import PlaceholdersTable
from helper import ms_to_time_str, time_str_to_ms, resource_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger

class ThumbnailSetter(QDialog):
    """
    A dialog for selecting a frame from a video to be used as a thumbnail.
    """

    def __init__(self, video_path: str, output_folder: str, logger: 'Logger', parent=None):
        """
        Initializes the ThumbnailSetter dialog.

        Args:
            video_path (str): The absolute path to the video file.
            output_folder (str): The path to the output directory.
            logger (Logger): An instance of the logger for displaying messages.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Set Video Thumbnail")
        self.setWindowIcon(QIcon(resource_path("icon/set-thumbnail.png")))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(950, 650)

        self._video_path = video_path
        self._logger = logger
        self._output_folder = output_folder
        self._placeholders = ThumbnailPlaceholders()

        self._controlled_player: ControlledPlayer
        self._action_panel: ActionPanel
        self._command_template: CommandTemplates
        self._placeholders_table: PlaceholdersTable

        self._processor = ThumbnailProcessor(self)
        self._is_closing = False

        self._setup_ui()
        self._connect_signals()
        self._update_ui_state('enable')

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self._controlled_player.load_media(self._video_path)

    def closeEvent(self, event):
        """Stops any running process and cleans up resources before closing."""
        # If a process is running, stop it and wait for it to finish
        # before actually closing the window.
        if self._processor.is_running():
            if not self._is_closing: # Prevent multiple stop signals
                self._is_closing = True
                self._processor.stop()
                event.ignore() # Ignore the close event for now
                return
        
        # If no process is running, or we are closing after a process has finished
        self._controlled_player.cleanup() # Clean up the media player
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Override to prevent Esc from closing the dialog, which can cause issues."""
        if event.key() == Qt.Key_Escape:
            event.accept() # Consume the event, do nothing
        else:
            super().keyPressEvent(event)

    def _setup_ui(self):
        """Initializes and lays out the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self._controlled_player = ControlledPlayer()
        self._action_panel = ActionPanel()
        self._placeholders_table = PlaceholdersTable(placeholders_list=self._placeholders.get_placeholders_list(),
                                                     num_columns=6,
                                                     parent=self
                                                     )
        self._placeholders_table.set_compact_height()

        self._command_template = CommandTemplates(placeholders=self._placeholders)
        self._command_template.setFixedHeight(100)

        main_layout.addWidget(self._controlled_player)
        main_layout.addWidget(self._action_panel)
        main_layout.addWidget(self._placeholders_table)
        main_layout.addWidget(self._command_template)

    def _connect_signals(self):
        """Connects signals and slots for the dialog's components."""
        self._action_panel.go_clicked.connect(self._on_go_to_timestamp)
        self._action_panel.run_clicked.connect(self._on_set_thumbnail)
        self._action_panel.stop_clicked.connect(self._stop_process)

        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)

        self._placeholders_table.placeholder_double_clicked.connect(self._command_template.insert_placeholder)

    @pyqtSlot()
    def _on_go_to_timestamp(self):
        """When the user clicks 'Go', seek the player to the manually entered time."""
        time_str = self._action_panel.get_timestamp_text()
        try:
            pos_ms = time_str_to_ms(time_str)
            if not (0 <= pos_ms <= self._controlled_player.duration()):
                raise ValueError("Time is out of video duration range.")
            self._controlled_player.set_position(pos_ms)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Time", f"Invalid timestamp format or value: {time_str}\n{e}")

    @pyqtSlot()
    def _on_set_thumbnail(self): 
        """When the user clicks 'Set Thumbnail', start the thumbnail process."""
        if self._processor.is_running():
            QMessageBox.warning(self, "In Progress", "A thumbnail operation is already in progress.")
            return
        
        # Use the current player position for setting the thumbnail
        timestamp = ms_to_time_str(self._controlled_player.position())
        
        # Disable button and pause video when processing
        self._update_ui_state('disable')
        self._controlled_player.pause()
        
        self._processor.start(
            input_file=self._video_path, 
            output_folder=self._output_folder, 
            cmd_template=self._command_template,
            timestamp = timestamp)

    @pyqtSlot()
    def _stop_process(self):
        """Stops the thumbnail process if it is running."""
        if self._processor.is_running():
            self._processor.stop()

    def _update_ui_state(self, state: str):
        """Enables or disables UI controls based on processing state."""
        if state == "enable":
            self._action_panel.update_ui_state('enable')
            self._controlled_player.setEnabled(True)
            self._placeholders_table.setEnabled(True)
            self._command_template.setEnabled(True)
        elif state == "disable":
            self._action_panel.update_ui_state('disable')
            self._controlled_player.setDisabled(True)
            self._placeholders_table.setDisabled(True)
            self._command_template.setDisabled(True)
        else:
            return

    @pyqtSlot()
    def _on_processing_finished(self):
        """Handles the completion of the thumbnail process."""
        # If the dialog was waiting to close, close it now.
        if self._is_closing:
            self.close()
            return
        self._update_ui_state('enable')

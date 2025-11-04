from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QRadioButton, QHBoxLayout,
                             QPushButton, QMessageBox, QSizePolicy)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QSize, pyqtSlot, Qt

from helper import resource_path
from .processor import VideoJoinerProcessor
from .command import CommandTemplate
from .placeholders import VideoJoinerPlaceholders
from components import PlaceholdersTable, StyledButton
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger

class VideoJoiner(QDialog):
    """A dialog for joining multiple video files."""
    def __init__(self, 
                 selected_files: list[tuple[int, str, str]], 
                 output_folder: str, 
                 logger: 'Logger', 
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Videos")
        self.setWindowIcon(QIcon(resource_path("icon/join-video.png")))
        self.setMinimumWidth(600)

        self._selected_files = selected_files
        self._output_folder = output_folder
        self._placeholders = VideoJoinerPlaceholders()
        self._logger = logger

        self._processor = VideoJoinerProcessor(self)

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        self._on_method_changed()

    def closeEvent(self, event):
        """Stops any running process before closing the dialog."""
        if self._processor.is_running():
            self._processor.stop()
        self._processor.wait() # Wait for the thread to finish cleanly
        super().closeEvent(event)

    def _create_widgets(self):
        """Creates all the widgets for the dialog."""
        # --- Join Method Selection ---
        self._concat_demuxer_radio = QRadioButton("Concat Demuxer (Fast, No Re-encoding)")
        self._concat_filter_radio = QRadioButton("Concat Filter (Slower, Re-encodes)")
        self._concat_demuxer_radio.setChecked(True)

        self._placeholders_table = PlaceholdersTable(
            placeholders_list=self._placeholders.get_placeholders_list(),
            num_columns=4,
            parent=self
        )
        self._placeholders_table.set_compact_height()
        disable_placeholder = [
            self._placeholders.get_INFILE_NAME(),
            self._placeholders.get_INFILE_EXT()
        ]
        self._placeholders_table.set_disabled_placeholders(disable_placeholder)

        self._cmd_template = CommandTemplate(placeholders=self._placeholders)

        min_height = 36
        self._join_video_button = StyledButton(
            text="Join Videos ",
            icon_name="join-video-button.png",
            icon_size=QSize(20, 20),
            min_height=min_height,
            padding=(12, 0, 12, 0),
            layout_direction=Qt.RightToLeft
        )
        self._stop_button = StyledButton(
            text=" Stop",
            icon_name="stop.png",
            icon_size=QSize(19, 19),
            min_height=min_height
        )

    def _setup_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        method_group = QGroupBox("Join Method")
        method_layout = QHBoxLayout()
        method_layout.addWidget(self._concat_demuxer_radio)
        method_layout.addWidget(self._concat_filter_radio)
        method_group.setLayout(method_layout)

        placeholder_group = QGroupBox("Placeholders")
        placeholder_layout = QVBoxLayout()
        placeholder_layout.addWidget(self._placeholders_table)
        placeholder_group.setLayout(placeholder_layout)

        cmd_template_group = QGroupBox("Command Template")
        cmd_template_layout = QVBoxLayout()
        cmd_template_layout.addWidget(self._cmd_template)
        cmd_template_group.setLayout(cmd_template_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self._join_video_button)
        button_layout.addWidget(self._stop_button)

        self.main_layout.addWidget(method_group)
        self.main_layout.addWidget(placeholder_group)
        self.main_layout.addWidget(cmd_template_group)
        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connects UI element signals to corresponding slots."""
        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)
        self._concat_demuxer_radio.toggled.connect(self._on_method_changed)
        self._join_video_button.clicked.connect(self._start_join_process)
        self._stop_button.clicked.connect(self._stop_join_process)
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)

    def _on_method_changed(self):
        """Updates the command template based on the selected join method."""
        method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"
        self._cmd_template.set_command_for_method(method)
        self._set_ui_enabled_for_processing(is_processing=False)

    def _start_join_process(self):
        """Initiates the video joining process."""
        if self._processor.is_running():
            QMessageBox.warning(self, "In Progress", "A joining process is already running.")
            return

        join_method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"

        self._set_ui_enabled_for_processing(is_processing=True)

        self._processor.start(
            selected_files=self._selected_files,
            output_folder=self._output_folder,
            cmd_template=self._cmd_template,
            join_method=join_method
        )

    @pyqtSlot()
    def _stop_join_process(self):
        """Stops the video joining process if it is running."""
        if self._processor.is_running():
            self._processor.stop()

    def _set_ui_enabled_for_processing(self, is_processing: bool):
        """Disables UI elements during processing, leaving only Stop enabled."""
        is_enabled = not is_processing
        self._join_video_button.setEnabled(is_enabled)
        self._concat_demuxer_radio.setEnabled(is_enabled)
        self._concat_filter_radio.setEnabled(is_enabled)
        self._placeholders_table.setEnabled(is_enabled)
        self._cmd_template.setEnabled(is_enabled)
        self._stop_button.setEnabled(is_processing)

    def _on_processing_finished(self):
        """Handles the completion of the joining process."""
        self._set_ui_enabled_for_processing(is_processing=False)

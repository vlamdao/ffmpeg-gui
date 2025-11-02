from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QRadioButton, QHBoxLayout,
                             QPushButton, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

from helper import resource_path
from .processor import VideoJoinerProcessor
from .command import CommandTemplate
from .placeholders import VideoJoinerPlaceholders
from components import PlaceholdersTable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger

class VideoJoiner(QDialog):
    """A dialog for joining multiple video files."""
    log_signal = pyqtSignal(str)

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

        self._join_video_button = QPushButton("Join Videos")
        self._join_video_button.setMinimumHeight(32)

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

        self.main_layout.addWidget(method_group)
        self.main_layout.addWidget(placeholder_group)
        self.main_layout.addWidget(cmd_template_group)
        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connects UI element signals to corresponding slots."""
        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template._cmd_input.insertPlainText)
        self._concat_demuxer_radio.toggled.connect(self._on_method_changed)
        self._join_video_button.clicked.connect(self._start_join_process)
        self._processor.log_signal.connect(self.log_signal)
        self._processor.processing_finished.connect(self._on_processing_finished)
        self.log_signal.connect(self._logger.append_log)

    def _on_method_changed(self):
        """Updates the command template based on the selected join method."""
        method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"
        self._cmd_template.set_command_for_method(method)

    def _start_join_process(self):
        """Initiates the video joining process."""
        if self._processor.is_running():
            QMessageBox.warning(self, "In Progress", "A joining process is already running.")
            return

        join_method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"

        self._join_video_button.setEnabled(False)
        self._join_video_button.setText("Joining...")

        self._processor.start(
            selected_files=self._selected_files,
            output_folder=self._output_folder,
            cmd_template=self._cmd_template,
            join_method=join_method
        )

    def _on_processing_finished(self, success: bool, message: str):
        """Handles the completion of the joining process."""
        self._join_video_button.setEnabled(True)
        self._join_video_button.setText("Join Videos")
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

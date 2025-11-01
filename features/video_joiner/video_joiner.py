import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QRadioButton, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
                             QPushButton, QMessageBox, QDialogButtonBox)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from helper import resource_path, FontDelegate
from helper.placeholders import VIDEO_JOINER_PLACEHOLDERS
from .processor import VideoJoinerProcessor
from components import PlaceholderTable

class VideoJoiner(QDialog):
    """A dialog for joining multiple video files."""
    log_signal = pyqtSignal(str)

    # Default command templates for each join method
    CONCAT_DEMUXER_CMD = 'ffmpeg -y -f concat -safe 0 -i "{concatfile_path}" -c copy "{output_folder}/joined_video.mp4"'
    CONCAT_FILTER_CMD = 'ffmpeg -y {inputs} -filter_complex "{filter_script}" -map "[v]" -map "[a]" "{output_folder}/joined_video_re-encoded.mp4"'

    def __init__(self, selected_files: list[tuple[int, str, str]], output_folder: str, logger, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Videos")
        self.setWindowIcon(QIcon(resource_path("icon/join-video.png")))
        self.setMinimumWidth(700)

        self._selected_files = selected_files
        self._output_folder = output_folder
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

        # --- Placeholders ---
        self._placeholder_table = PlaceholderTable(
            placeholders=VIDEO_JOINER_PLACEHOLDERS,
            num_columns=4,
            parent=self
        )
        self._placeholder_table.set_compact_height()

        # --- Command Template ---
        self._cmd_input = QTextEdit()
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumHeight(80)

        # --- Action Buttons ---
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
        placeholder_layout = QVBoxLayout(placeholder_group)
        placeholder_layout.addWidget(self._placeholder_table)

        command_group = QGroupBox("Command Template")
        command_layout = QVBoxLayout(command_group)
        command_layout.addWidget(self._cmd_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self._join_video_button)

        self.main_layout.addWidget(method_group)
        self.main_layout.addWidget(placeholder_group)
        self.main_layout.addWidget(command_group)
        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connects UI element signals to corresponding slots."""
        self._concat_demuxer_radio.toggled.connect(self._on_method_changed)
        self._concat_filter_radio.toggled.connect(self._on_method_changed)
        self._placeholder_table.placeholder_double_clicked.connect(self._cmd_input.insertPlainText)
        self._join_video_button.clicked.connect(self._start_join_process)
        self._processor.log_signal.connect(self.log_signal)
        self._processor.processing_finished.connect(self._on_processing_finished)
        self.log_signal.connect(self._logger.append_log)

    def _on_method_changed(self):
        """Updates the command template based on the selected join method."""
        if self._concat_demuxer_radio.isChecked():
            self._cmd_input.setText(self.CONCAT_DEMUXER_CMD)
        else:
            self._cmd_input.setText(self.CONCAT_FILTER_CMD)

    def _start_join_process(self):
        """Initiates the video joining process."""
        if self._processor.is_running():
            QMessageBox.warning(self, "In Progress", "A joining process is already running.")
            return

        command_template = self._cmd_input.toPlainText().strip()
        if not command_template:
            QMessageBox.critical(self, "Error", "Command template cannot be empty.")
            return

        join_method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"

        self._join_video_button.setEnabled(False)
        self._join_video_button.setText("Joining...")

        self._processor.start(
            selected_files=self._selected_files,
            output_folder=self._output_folder,
            command_template=command_template,
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

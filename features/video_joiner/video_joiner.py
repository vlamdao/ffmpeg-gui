from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QRadioButton, QHBoxLayout,
                             QPushButton, QMessageBox, QSizePolicy)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QSize, pyqtSlot, Qt

from helper import resource_path
from .processor import VideoJoinerProcessor
from .command import CommandTemplate
from .placeholders import VideoJoinerPlaceholders
from components import PlaceholdersTable, StyledButton
from .action_panel import ActionPanel
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
        self._placeholders_table.set_disabled_placeholders([self._placeholders.get_INFILE_NAME(),
                                                            self._placeholders.get_INFILE_EXT()])

        self._cmd_template = CommandTemplate(placeholders=self._placeholders)
        self._action_panel = ActionPanel()

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

        self.main_layout.addWidget(method_group)
        self.main_layout.addWidget(placeholder_group)
        self.main_layout.addWidget(cmd_template_group)
        self.main_layout.addWidget(self._action_panel)

    def _connect_signals(self):
        """Connects UI element signals to corresponding slots."""
        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)
        self._concat_demuxer_radio.toggled.connect(self._on_method_changed)
        self._action_panel.run_clicked.connect(self._start_join_process)
        self._action_panel.stop_clicked.connect(self._stop_join_process)
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)

    def _on_method_changed(self):
        """Updates the command template based on the selected join method."""
        method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"
        self._cmd_template.set_command_for_method(method)
        self._disable_ui_while_processing(is_disable=False)

    def _start_join_process(self):
        """Initiates the video joining process."""
        if self._processor.is_running():
            QMessageBox.warning(self, "In Progress", "A joining process is already running.")
            return

        join_method = "demuxer" if self._concat_demuxer_radio.isChecked() else "filter"

        self._disable_ui_while_processing(is_disable=True)

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

    def _disable_ui_while_processing(self, is_disable: bool):
        """Disables UI elements during processing, leaving only Stop enabled."""
        self._concat_demuxer_radio.setEnabled(not is_disable)
        self._concat_filter_radio.setEnabled(not is_disable)
        self._placeholders_table.setEnabled(not is_disable)
        self._cmd_template.setEnabled(not is_disable)
        self._action_panel.disable_action_panel(is_disable)

    def _on_processing_finished(self):
        """Handles the completion of the joining process."""
        self._disable_ui_while_processing(is_disable=False)

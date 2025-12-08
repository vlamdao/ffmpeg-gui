from PyQt5.QtWidgets import QDialog, QWidget
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QCloseEvent
from features.player import ControlledPlayer

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger
    from .processor import BaseProcessor
    from components import PlaceholdersTable
    from .command import BaseCommandTemplate
    from .action_panel import BaseActionPanel

class BasePlayerDialog(QDialog):
    """
    A base dialog for features that include a video player.

    This class encapsulates common functionalities such as:
    - Handling the lifecycle of a background processor (_processor).
    - Managing a video player (_controlled_player).
    - Gracefully handling the close event to stop running processes.
    - Updating UI state (enabled/disabled) during processing.
    - Loading the media when the dialog is shown.
    """
    def __init__(self, 
                 video_path: str, 
                 output_folder: str, 
                 logger: 'Logger', 
                 parent: QWidget = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(800, 600)

        self._video_path = video_path
        self._output_folder = output_folder
        self._logger = logger
        self._is_closing = False

        # Common components are instantiated here.
        self._controlled_player: ControlledPlayer = ControlledPlayer(self)
        self._processor: 'BaseProcessor' = None
        self._placeholders_table: 'PlaceholdersTable' = None
        self._cmd_template: 'BaseCommandTemplate' = None
        self._action_panel: 'BaseActionPanel' = None

    def _setup_base_ui(self):
        """Subclasses should call this after creating their widgets."""
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._update_ui_state('enable')

    def _create_widgets(self):
        self._controlled_player = ControlledPlayer()
        # Subclasses should create other widgets here.

    def _setup_layout(self):
        """Subclasses must implement this to arrange widgets in the dialog."""
        raise NotImplementedError("Subclasses must implement _setup_layout.")

    def _connect_signals(self):
        """Subclasses should call super()._connect_signals() and add their own connections."""
        if not all([self._processor, self._logger, self._action_panel, self._placeholders_table, self._cmd_template]):
            raise NotImplementedError("All required widgets must be initialized before connecting signals.")
        
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)

        self._action_panel.stop_clicked.connect(self._stop_process)

        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)

    def showEvent(self, event):
        """Load media when the dialog is shown."""
        super().showEvent(event)
        if self._controlled_player:
            self._controlled_player.load_media(self._video_path)

    def closeEvent(self, event: QCloseEvent):
        """Stop any running process before closing."""
        if self._processor and self._processor.is_running():
            if not self._is_closing:
                self._is_closing = True
                self._processor.stop()
                event.ignore()
                return
        
        if self._controlled_player:
            self._controlled_player.cleanup()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Prevent Esc from closing the dialog."""
        if event.key() == Qt.Key_Escape:
            event.accept()
        else:
            super().keyPressEvent(event)

    def _run_process(self):
        """Subclasses must implement this to arrange widgets in the dialog."""
        raise NotImplementedError("Subclasses must implement _run_process.")

    @pyqtSlot()
    def _stop_process(self):
        if self._processor and self._processor.is_running():
            self._processor.stop()

    def _update_ui_state(self, state: str):
        """Enable or disable UI controls based on processing state."""
        is_disabled = (state == "disable")
        
        if hasattr(self._action_panel, 'update_ui_state'):
            self._action_panel.update_ui_state('enable' if not is_disabled else 'disable')

        if self._controlled_player:
            self._controlled_player.setDisabled(is_disabled)

        if self._placeholders_table:
            self._placeholders_table.setDisabled(is_disabled)

        if self._cmd_template:
            self._cmd_template.setDisabled(is_disabled)

    @pyqtSlot()
    def _on_processing_finished(self):
        """Handle the completion of the process."""
        if self._is_closing:
            self.close()
            return
        self._update_ui_state('enable')
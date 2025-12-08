from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QMessageBox, QWidget,
                             QLineEdit, QLabel)
from PyQt5.QtCore import Qt, QRectF, pyqtSlot, QRect, QEvent, QPoint
from PyQt5.QtGui import QIcon, QPainter, QPen, QColor, QPainterPath

from helper import resource_path
from components import PlaceholdersTable
from .processor import VideoCropperProcessor
from features.player import ControlledPlayer
from .components import (ActionPanel, CommandTemplate, VideoCropperPlaceholders, OverlayWidget)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger


class VideoCropper(QDialog):
    def __init__(self, video_path: str, output_folder: str, logger: 'Logger', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cropper")
        self.setWindowIcon(QIcon(resource_path("icon/crop-video.png")))
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_DeleteOnClose) # Ensure cleanup when closed non-modally
        self.setMinimumSize(800, 600)

        self._video_path = video_path
        self._output_folder = output_folder
        self._logger = logger
        self._placeholders = VideoCropperPlaceholders()
        self._processor = VideoCropperProcessor(self)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self._controlled_player = ControlledPlayer(self)
        self._placeholders_table = PlaceholdersTable(
            placeholders_list=self._placeholders.get_placeholders_list(),
            num_columns=6,
            parent=self
        )
        self._placeholders_table.set_compact_height()

        self._cmd_template = CommandTemplate(placeholders=self._placeholders)
        self._cmd_template.setFixedHeight(90)

        self._action_panel = ActionPanel()

        main_layout.addWidget(self._controlled_player, 1)
        main_layout.addWidget(self._placeholders_table)
        main_layout.addWidget(self._cmd_template)
        main_layout.addWidget(self._action_panel)

        # Overlay for crop selection
        self._overlay = OverlayWidget(self)

    def _connect_signals(self):
        # Feature-specific actions
        self._action_panel.run_clicked.connect(self._start_crop_process)
        self._action_panel.stop_clicked.connect(self._stop_crop_process)
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)
        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)

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
        # Ensure the overlay is closed when the main dialog closes
        if hasattr(self, '_overlay'):
            self._overlay.close()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Override to prevent Esc from closing the dialog, which can cause issues."""
        if event.key() == Qt.Key_Escape:
            event.accept() # Consume the event, do nothing
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # Load media when the dialog is shown to avoid blocking the UI on init
        self._controlled_player.load_media(self._video_path)
        # When the dialog is shown, show and position the overlay
        self._update_overlay_geometry()
        self._overlay.show()

    def moveEvent(self, event):
        super().moveEvent(event)
        # Update overlay position when the main window moves
        if hasattr(self, '_controlled_player'):
            self._update_overlay_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update overlay position and size when the main window is resized
        if hasattr(self, '_controlled_player'):
            self._update_overlay_geometry()

    def changeEvent(self, event):
        """
        Handles window state changes to show/hide the overlay accordingly.
        """
        super().changeEvent(event)
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                if not self.isMinimized():
                    self._overlay.show()
            else:
                self._overlay.hide()
        elif event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                self._overlay.hide()

    def _update_overlay_geometry(self):
        """Positions the overlay widget exactly on top of the video widget."""
        video_widget = self._controlled_player.get_video_widget()
        # Map the video widget's rectangle to global coordinates
        top_left_global = video_widget.mapToGlobal(video_widget.rect().topLeft())
        # Set the overlay's geometry based on the global position and size
        self._overlay.setGeometry(top_left_global.x(), top_left_global.y(), video_widget.width(), video_widget.height())

    def _start_crop_process(self):
        # --- Calculate final crop parameters here, just before running ---
        video_width, video_height = self._controlled_player.get_video_resolution()
        if video_width == 0 or video_height == 0:
            QMessageBox.warning(self, "Error", "Could not determine video resolution. Please play the video first.")
            return
        video_widget = self._controlled_player.get_video_widget()
        widget_width = video_widget.width()
        widget_height = video_widget.height()

        # The resizable rectangle's geometry is relative to the video widget
        rect = self._overlay.get_crop_geometry()

        # Calculate scaling factors
        scale_x = video_width / widget_width
        scale_y = video_height / widget_height

        # Calculate the real crop parameters based on the video's native resolution
        final_w = int(rect.width() * scale_x) - (int(rect.width() * scale_x) % 2) # Ensure even number
        final_h = int(rect.height() * scale_y)
        final_x = int(rect.x() * scale_x)
        final_y = int(rect.y() * scale_y)

        crop_params = {
            'w': str(final_w), 'h': str(final_h),
            'x': str(final_x), 'y': str(final_y)
        }

        log_msg = f"Crop parameters: w={final_w}, h={final_h}, x={final_x}, y={final_y}"
        self._logger.append_log(log_msg)

        if not all(crop_params.values()):
            QMessageBox.warning(self, "Input Error", "All crop parameters must be filled.")
            return

        self._action_panel.update_ui_state('disable')
        self._processor.start(self._video_path, self._output_folder, self._cmd_template, crop_params)

    def _stop_crop_process(self):
        self._processor.stop()

    @pyqtSlot()
    def _on_processing_finished(self):
        self._action_panel.update_ui_state('enable')
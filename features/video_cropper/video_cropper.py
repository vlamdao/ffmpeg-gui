from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QMessageBox, QWidget,
                             QLineEdit, QLabel)
from PyQt5.QtCore import Qt, QRectF, pyqtSlot, QRect, QEvent, QPoint
from PyQt5.QtGui import QIcon, QPainter, QPen, QColor, QPainterPath

from helper import resource_path
from components import PlaceholdersTable
from .processor import VideoCropperProcessor
from features.player import MediaPlayer, MediaControls
from .components import (ActionPanel, CommandTemplate, VideoCropperPlaceholders, OverlayWidget)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger


class VideoCropper(QDialog):
    def __init__(self, video_path: str, output_folder: str, logger: 'Logger', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cropper")
        self.setWindowIcon(QIcon(resource_path("icon/crop-video.png")))
        self.setAttribute(Qt.WA_DeleteOnClose) # Ensure cleanup when closed non-modally
        self.setMinimumSize(800, 600)

        self._video_path = video_path
        self._output_folder = output_folder
        self._logger = logger
        self._placeholders = VideoCropperPlaceholders()
        self._processor = VideoCropperProcessor(self)

        self._setup_ui()
        self._connect_signals()

        self._media_player.load_media(self._video_path)

    def closeEvent(self, event):
        self._media_player.cleanup()
        # Ensure the overlay is closed when the main dialog closes
        if hasattr(self, '_overlay'):
            self._overlay.close()
        super().closeEvent(event)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Create a container for the player and the overlay
        player_container = QWidget()
        player_container_layout = QVBoxLayout(player_container)
        player_container_layout.setContentsMargins(0, 0, 0, 0)

        self._media_player = MediaPlayer(self)
        player_container_layout.addWidget(self._media_player)

        # Create the separate overlay widget
        self._overlay = OverlayWidget()

        self._media_controls = MediaControls()
        
        self._placeholders_table = PlaceholdersTable(
            placeholders_list=self._placeholders.get_placeholders_list(),
            num_columns=6,
            parent=self
        )
        self._placeholders_table.set_compact_height()

        self._cmd_template = CommandTemplate(placeholders=self._placeholders)
        self._action_panel = ActionPanel()

        main_layout.addWidget(player_container, 1)
        main_layout.addWidget(self._media_controls)
        main_layout.addWidget(self._placeholders_table)
        main_layout.addWidget(self._cmd_template)
        main_layout.addWidget(self._action_panel)

    def showEvent(self, event):
        super().showEvent(event)
        # When the dialog is shown, show and position the overlay
        self._update_overlay_geometry()
        self._overlay.show()

    def moveEvent(self, event):
        super().moveEvent(event)
        # Update overlay position when the main window moves
        if hasattr(self, '_media_player'):
            self._update_overlay_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update overlay position and size when the main window is resized
        if hasattr(self, '_media_player'):
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

    def _connect_signals(self):
        # Player controls
        self._media_controls.play_clicked.connect(self._media_player.toggle_play)
        self._media_controls.seek_backward_clicked.connect(self._media_player.seek_backward)
        self._media_controls.seek_forward_clicked.connect(self._media_player.seek_forward)
        self._media_controls.seek_requested.connect(self._media_player.set_position)

        # Player state updates
        self._media_player.media_loaded.connect(self._media_controls.set_play_button_enabled)
        self._media_player.state_changed.connect(self._media_controls.update_media_state)
        self._media_player.position_changed.connect(
            lambda pos: self._media_controls.update_position(pos, self._media_player.duration())
        )
        self._media_player.duration_changed.connect(self._media_controls.update_duration)

        # Feature-specific actions
        self._action_panel.run_clicked.connect(self._start_crop_process)
        self._action_panel.stop_clicked.connect(self._stop_crop_process)
        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)
        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)

    def _update_overlay_geometry(self):
        """Positions the overlay widget exactly on top of the video widget."""
        video_widget = self._media_player.get_video_widget()
        # Map the video widget's rectangle to global coordinates
        top_left_global = video_widget.mapToGlobal(video_widget.rect().topLeft())
        # Set the overlay's geometry based on the global position and size
        self._overlay.setGeometry(top_left_global.x(), top_left_global.y(), video_widget.width(), video_widget.height())

    def _start_crop_process(self):
        # --- Calculate final crop parameters here, just before running ---
        video_width, video_height = self._media_player.get_video_resolution()
        if video_width == 0 or video_height == 0:
            QMessageBox.warning(self, "Error", "Could not determine video resolution. Please play the video first.")
            return
        video_widget = self._media_player.get_video_widget()
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
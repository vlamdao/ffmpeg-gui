from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QMessageBox, QWidget,
                             QLineEdit, QLabel)
from PyQt5.QtCore import Qt, QRectF, pyqtSlot, QRect, QEvent, QPoint
from PyQt5.QtGui import QIcon, QPainter, QPen, QColor, QPainterPath, QCloseEvent

from helper import resource_path, ms_to_time_str, time_str_to_ms
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

        self._is_closing = False
        self._segment = {'start': 0, 'end': 0}

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
        self._action_panel = ActionPanel()

        main_layout.addWidget(self._controlled_player, 1)
        main_layout.addWidget(self._action_panel)
        main_layout.addWidget(self._placeholders_table)
        main_layout.addWidget(self._cmd_template)
        
        # Overlay for crop selection
        self._overlay = OverlayWidget(self)
        self._overlay.setEnabled(False) # Disable overlay initially. It will be enabled when the media is ready.

    def _connect_signals(self):
        # Feature-specific actions
        self._action_panel.run_clicked.connect(self._on_crop_video)
        self._action_panel.stop_clicked.connect(self._stop_process)
        self._action_panel.set_start_clicked.connect(self._on_set_start_time)
        self._action_panel.set_end_clicked.connect(self._on_set_end_time)

        self._processor.log_signal.connect(self._logger.append_log)
        self._processor.processing_finished.connect(self._on_processing_finished)

        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)
        
        # Update overlay and end time when media duration is known (which means metadata is loaded)
        self._controlled_player._media_player.duration_changed.connect(self._on_media_ready)

    def closeEvent(self, event: QCloseEvent):
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

    @pyqtSlot('qint64')
    def _on_media_ready(self, duration: int):
        """Called when the media is parsed and its properties are known."""
        self._segment = {'start': 0, 'end': duration}
        self._update_segment_label_marker()

        self._overlay.setEnabled(True) # Enable drawing now that we have correct dimensions
        self._update_overlay_geometry()
        self._overlay.show() # Ensure overlay is visible after geometry update

    def _calculate_video_rect_in_widget(self) -> QRect:
        """
        Calculates the actual rectangle where the video is rendered within the video widget,
        accounting for letterboxing or pillarboxing.
        """
        video_widget = self._controlled_player.get_video_widget()
        widget_width = video_widget.width()
        widget_height = video_widget.height()

        video_width, video_height = self._controlled_player.get_video_resolution()

        if video_width == 0 or video_height == 0:
            return video_widget.rect() # Fallback to full widget if resolution is unknown

        widget_aspect = widget_width / widget_height
        video_aspect = video_width / video_height

        if video_aspect > widget_aspect: # Video is wider than widget (letterboxing)
            render_width = widget_width
            render_height = int(render_width / video_aspect)
            x_offset = 0
            y_offset = (widget_height - render_height) // 2
        else: # Video is taller than widget (pillarboxing)
            render_height = widget_height
            render_width = int(render_height * video_aspect)
            x_offset = (widget_width - render_width) // 2
            y_offset = 0
            
        return QRect(x_offset, y_offset, render_width, render_height)

    def _update_overlay_geometry(self):
        """Positions the overlay widget exactly on top of the video's actual render area."""
        video_widget = self._controlled_player.get_video_widget()
        
        # Calculate the actual video rendering area within the widget
        video_rect_in_widget = self._calculate_video_rect_in_widget()

        # Map the calculated video rect to global coordinates
        top_left_global = video_widget.mapToGlobal(video_rect_in_widget.topLeft())
        
        # Set the overlay's geometry to match the video's render area
        self._overlay.update_geometry_and_crop_rect(QRect(top_left_global, video_rect_in_widget.size()))

    def _on_crop_video(self):
        # --- Calculate final crop parameters here, just before running ---
        video_width, video_height = self._controlled_player.get_video_resolution()
        if video_width == 0 or video_height == 0:
            QMessageBox.warning(self, "Error", "Could not determine video resolution. Please play the video first.")
            return
        
        # The overlay's geometry now matches the rendered video area.
        rendered_video_rect = self._overlay.geometry()
        # The crop selection rectangle is relative to the overlay.
        rect = self._overlay.get_crop_geometry()

        # Calculate scaling factors
        scale_x = video_width / rendered_video_rect.width()
        scale_y = video_height / rendered_video_rect.height()

        print(f"Video resolution: {video_width}x{video_height}")
        print(f"Rendered video size: {rendered_video_rect.width()}x{rendered_video_rect.height()}")
        print(f"Scale factors: x={scale_x}, y={scale_y}")
        print(f"Selected rectangle (overlay coords): x={rect.x()}, y={rect.y()}, w={rect.width()}, h={rect.height()}")
        

        # Calculate the real crop parameters based on the video's native resolution
        final_w = int(rect.width() * scale_x)
        final_h = int(rect.height() * scale_y) - (int(rect.height() * scale_y) % 2) # Ensure even number for height
        final_x = int(rect.x() * scale_x)
        final_y = int(rect.y() * scale_y)

        crop_params = {
            'w': str(final_w), 'h': str(final_h),
            'x': str(final_x), 'y': str(final_y)
        }

        log_msg = f"Crop parameters: w={final_w}, h={final_h}, x={final_x}, y={final_y}"
        self._logger.append_log(log_msg)

        self._controlled_player.pause()
        self._update_ui_state('disable')

        # self._processor.start(self._video_path, self._output_folder, self._cmd_template, crop_params)
        self._processor.start(
            input_file=self._video_path, 
            output_folder=self._output_folder, 
            cmd_template=self._cmd_template,
            crop_params=crop_params,
            start_time=ms_to_time_str(self._segment['start']),
            end_time=ms_to_time_str(self._segment['end']))
    
    @pyqtSlot()
    def _on_set_start_time(self):
        """Sets the start time from the player's current position."""
        new_start_ms = self._controlled_player.position()
        
        if new_start_ms > self._segment['end']:
            self._segment['end'] = self._controlled_player.duration()
        
        self._segment['start'] = new_start_ms
        self._update_segment_label_marker()

    @pyqtSlot()
    def _on_set_end_time(self):
        """Sets the end time from the player's current position."""
        new_end_ms = self._controlled_player.position()

        if new_end_ms < self._segment['start']:
            QMessageBox.warning(self, "Invalid Time", "End time cannot be before start time.")
            self._controlled_player.set_position(self._segment['end'])
            return
        
        self._segment['end'] = new_end_ms
        self._update_segment_label_marker()

    @pyqtSlot()
    def _stop_process(self):
        if self._processor.is_running():
            self._processor.stop()

    def _update_ui_state(self, state: str):
        """Enables or disables UI controls based on processing state."""
        if state == "enable":
            self._action_panel.update_ui_state('enable')
            self._controlled_player.setEnabled(True)
            self._placeholders_table.setEnabled(True)
            self._cmd_template.setEnabled(True)
            self._overlay.setEnabled(True)
        elif state == "disable":
            self._action_panel.update_ui_state('disable')
            self._controlled_player.setDisabled(True)
            self._placeholders_table.setDisabled(True)
            self._cmd_template.setDisabled(True)
            self._overlay.setDisabled(True)
        else:
            return

    @pyqtSlot()
    def _on_processing_finished(self):
        # If the dialog was waiting to close, close it now.
        if self._is_closing:
            self.close()
            return
        self._update_ui_state('enable')

    def _update_segment_label_marker(self):
        """Synchronizes the UI with the internal segment state."""
        # self._action_panel.set_segment_label(f'{ms_to_time_str(self._segment['start'])} - {ms_to_time_str(self._segment['end'])}')
        self._action_panel.set_segment_label(f"{ms_to_time_str(self._segment['start'])} - {ms_to_time_str(self._segment['end'])}")
        self._controlled_player.set_segment_markers([(self._segment['start'], self._segment['end'])])
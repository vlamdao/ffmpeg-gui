from PyQt5.QtWidgets import (QVBoxLayout, QMessageBox, QWidget)
from PyQt5.QtCore import Qt, pyqtSlot, QRect, QEvent
from PyQt5.QtGui import QIcon

from helper import resource_path, ms_to_time_str, time_str_to_ms
from components import PlaceholdersTable
from features.base.dialog import BasePlayerDialog
from .processor import VideoCropperProcessor
from .components import (VideoCropperActionPanel, VideoCropperCommandTemplate, VideoCropperPlaceholders, OverlayWidget)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger

class VideoCropper(BasePlayerDialog):
    def __init__(self, video_path: str, output_folder: str, logger: 'Logger', parent=None):
        super().__init__(video_path=video_path, output_folder=output_folder, logger=logger, parent=parent)
        self.setWindowTitle("Video Cropper")
        self.setWindowIcon(QIcon(resource_path("icon/crop-video.png")))
        self.setWindowModality(Qt.WindowModal)
        self.resize(900, 769)

        self._segment = {'start': 0, 'end': 0}

        self._setup_base_ui()

    def _create_widgets(self):
        """Instantiate feature-specific widgets."""
        self._placeholders = VideoCropperPlaceholders(self)
        self._processor = VideoCropperProcessor(self)
        self._action_panel = VideoCropperActionPanel(self)
        self._cmd_template = VideoCropperCommandTemplate(placeholders=self._placeholders)
        self._placeholders_table = PlaceholdersTable(
            placeholders_list=self._placeholders.get_placeholders_list(),
            num_columns=6,
            parent=self
        )
        self._placeholders_table.set_compact_height()
        self._overlay = OverlayWidget(self)
        self._overlay.setEnabled(False)

    def _setup_layout(self):
        """Set up the layout for the dialog."""
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._controlled_player, 1)
        main_layout.addWidget(self._action_panel)
        main_layout.addWidget(self._placeholders_table)
        main_layout.addWidget(self._cmd_template)

    def _connect_signals(self):
        """Connect signals for feature-specific widgets."""
        super()._connect_signals()
        # Feature-specific actions
        self._action_panel.run_clicked.connect(self._on_crop_video)
        self._action_panel.set_start_clicked.connect(self._on_set_start_time)
        self._action_panel.set_end_clicked.connect(self._on_set_end_time)
        
        # Update overlay and end time when media duration is known (which means metadata is loaded)
        self._controlled_player._media_player.duration_changed.connect(self._on_media_ready)

    def closeEvent(self, event):
        """Handle closing the dialog, ensuring the overlay is also closed."""
        super().closeEvent(event)
        # Ensure the overlay is closed when the main dialog closes
        if hasattr(self, '_overlay'):
            self._overlay.close()

    def showEvent(self, event):
        """Load media and show the overlay when the dialog is shown."""
        super().showEvent(event)
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

    def _update_ui_state(self, state: str):
        """Enables or disables UI controls based on processing state."""
        super()._update_ui_state(state)
        is_disabled = (state == "disable")
        if hasattr(self, '_overlay'):
            self._overlay.setDisabled(is_disabled)

    def _update_segment_label_marker(self):
        """Synchronizes the UI with the internal segment state."""
        segment_label_str = f"{ms_to_time_str(self._segment['start'])} - {ms_to_time_str(self._segment['end'])} | "
        segment_label_str += f"{ms_to_time_str(self._segment['end'] - self._segment['start'])}"
        
        self._action_panel.set_segment_label(segment_label_str)
        self._controlled_player.set_segment_markers([(self._segment['start'], self._segment['end'])])
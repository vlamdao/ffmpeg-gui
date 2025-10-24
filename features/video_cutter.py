import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QSlider, QListWidget, QWidget, QStyle,
                             QMessageBox, QLabel, QListWidgetItem, QSizePolicy, QStyleOptionSlider,
                             QSplitter, QMenu, QFormLayout, QTimeEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt, QUrl, QTime, QRect, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from processor import FFmpegWorker
from components import FontDelegate

_MARKER_COLOR = QColor(0, 120, 215, 100)

class DeselectableListWidget(QListWidget):
    """A QListWidget that clears selection when clicking on an empty area."""
    def mousePressEvent(self, event):
        # If we click on an empty area, clear the selection.
        # This will trigger the itemSelectionChanged signal.
        if not self.itemAt(event.pos()):
            self.clearSelection()
        # Call the base class implementation to handle normal item clicks.
        super().mousePressEvent(event)

class MarkerSlider(QSlider):
    """A custom QSlider that can draw markers for video segments."""
    
    def __init__(self, orientation):
        super().__init__(orientation)
        self.segment_markers = [] # List of (start_ms, end_ms) tuples
        self.current_start_marker_ms = -1 # Single start_ms for the temporary marker

    def set_segment_markers(self, markers):
        """Sets the list of markers to be drawn.

        Args:
            markers (list[tuple[int, int]]): A list of (start_ms, end_ms) tuples.
        """
        self.segment_markers = markers
        self.update() # Trigger a repaint

    def set_current_start_marker(self, start_ms):
        """Sets the position of the temporary start marker."""
        self.current_start_marker_ms = start_ms
        self.update() # Trigger a repaint

    def paintEvent(self, event):
        """Override paintEvent to draw markers on the slider track."""
        super().paintEvent(event) # Draw the slider first

        painter = QPainter(self)
        # Use a semi-transparent color for the markers
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)

        # Draw completed segment markers
        if self.segment_markers:
            painter.setBrush(_MARKER_COLOR) # Blue color for segments
            painter.setPen(Qt.NoPen)
            for start_ms, end_ms in self.segment_markers:
            # Calculate the pixel position for the start and end of the segment
                start_pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), start_ms, groove_rect.width())
                end_pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), end_ms, groove_rect.width())
                
                # Draw a rectangle for the segment
                marker_height = groove_rect.height() # Should be 16px from stylesheet
                marker_rect = QRect(groove_rect.x() + start_pos, groove_rect.y(), end_pos - start_pos, marker_height)
                painter.drawRect(marker_rect)

        # Draw current start marker
        if self.current_start_marker_ms != -1:
            painter.setBrush(_MARKER_COLOR) # Red color for start marker
            painter.setPen(Qt.NoPen) # Red border
            
            start_pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), self.current_start_marker_ms, groove_rect.width())
            
            # Draw a thin vertical line or a small rectangle
            marker_width = 2 # A thin line
            marker_height = groove_rect.height()
            marker_rect = QRect(groove_rect.x() + start_pos - marker_width // 2, groove_rect.y(), marker_width, marker_height)
            painter.drawRect(marker_rect)

    def mousePressEvent(self, event):
        """Override mousePressEvent to allow jumping to a position by clicking on the groove."""
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
            handle_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

            # Check if the click is on the groove, but not on the handle.
            if groove_rect.contains(event.pos()) and not handle_rect.contains(event.pos()):
                if self.orientation() == Qt.Horizontal:
                    pos_in_groove = event.pos().x() - groove_rect.x()
                    value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos_in_groove, groove_rect.width())
                else: # Vertical
                    pos_in_groove = event.pos().y() - groove_rect.y()
                    value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos_in_groove, groove_rect.height())
                
                self.setValue(value)
                # Manually trigger the action that sliderReleased would have done
                self.sliderReleased.emit()

        # Let the base class handle the event for dragging the handle
        super().mousePressEvent(event)

class EditSegmentDialog(QDialog):
    """A dialog for editing the start and end times of a video segment."""
    def __init__(self, parent, initial_start_ms, initial_end_ms):
        super().__init__(parent)
        self.setWindowTitle("Edit Segment")
        self.setMinimumWidth(300)

        self.start_time_edit = QTimeEdit(self)
        self.end_time_edit = QTimeEdit(self)
        # Set display format to include milliseconds
        self.start_time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.end_time_edit.setDisplayFormat("HH:mm:ss.zzz")

        # Set initial values
        self.start_time_edit.setTime(QTime.fromMSecsSinceStartOfDay(initial_start_ms))
        self.end_time_edit.setTime(QTime.fromMSecsSinceStartOfDay(initial_end_ms))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Start Time:", self.start_time_edit)
        layout.addRow("End Time:", self.end_time_edit)
        layout.addWidget(buttons)

    def get_edited_times(self):
        """Returns the start and end times (in milliseconds) from the input fields."""
        start_ms = self.start_time_edit.time().msecsSinceStartOfDay()
        end_ms = self.end_time_edit.time().msecsSinceStartOfDay()
        return start_ms, end_ms

    def accept(self):
        """Override accept to add validation before closing the dialog."""
        start_ms, end_ms = self.get_edited_times()
        if start_ms >= end_ms:
            QMessageBox.warning(self, "Invalid Times", "Start time must be before end time.")
            return
        super().accept()

class VideoCutter(QDialog):

    def __init__(self, video_path, output_path, logger, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cutter")
        # Add maximize and minimize buttons to the dialog window
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        self.setMinimumSize(1200, 600)
        # Dependencies
        self.video_path = video_path
        self.logger = logger
        self.output_path = output_path

        # State
        self.segments = []
        self.start_time = None
        self.end_time = None
        self._media_loaded = False
        self.active_workers = []
        self.frame_step_ms = 500 # Step 0.5 seconds
        self.selected_segment_index = -1 # -1 means no segment is selected for editing
        
        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        if not self._media_loaded:
            if os.path.exists(self.video_path):
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_path)))
                self.play_button.setEnabled(True)
                self._media_loaded = True
                self.media_player.play()
            else:
                QMessageBox.critical(self, "Error", f"Video file not found:\n{self.video_path}")
                self.play_button.setEnabled(False)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player and release resources."""
        self.media_player.stop()
        super().closeEvent(event)

    def _setup_ui(self):
        # Main layout is now horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel for video and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Video display
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(300)
        left_layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # Media controls
        media_controls = QWidget()
        controls_layout = QHBoxLayout(media_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        media_controls.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.previous_frame_button = QPushButton()
        self.previous_frame_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setEnabled(False)

        self.next_frame_button = QPushButton()
        self.next_frame_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))

        self.position_slider = MarkerSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setPageStep(1000) # Jump 1 second when clicking on the groove
        self.position_slider.setStyleSheet("""
            /* slider appearance */                                           
            QSlider::groove:horizontal {
                height: 16px;
                background-color: #b5b5b5;
            }
            /* handle appearance */
            QSlider::handle:horizontal {
                background-color: #0078D7;
                width: 8px;
                height: 48px; /* Match button height */
                margin: -3px 0; /* Center handle on groove */
            }
            /* QSlider::handle:horizontal:hover {
                 background-color: #0046a1;
             } */
        """)

        self.time_label = QLabel("00:00:00 / 00:00:00")

        controls_layout.addWidget(self.previous_frame_button) # Add previous frame button
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_frame_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.time_label)
        left_layout.addWidget(media_controls)

        # Segment definition
        segment_controls = QWidget()
        segment_layout = QHBoxLayout(segment_controls)
        segment_layout.setContentsMargins(0, 0, 0, 0)
        segment_controls.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.set_start_button = QPushButton("Set Start")
        self.set_end_button = QPushButton("Set End")
        self.cut_button = QPushButton("Cut Segments")

        self.start_label = QLabel("Start: --:--:--.---")
        self.start_label.setFixedWidth(120) # Increased width to accommodate milliseconds
        self.end_label = QLabel("End: --:--:--.---")
        self.end_label.setFixedWidth(120) # Increased width to accommodate milliseconds

        segment_layout.addWidget(self.set_start_button)
        segment_layout.addWidget(self.start_label)
        segment_layout.addWidget(self.set_end_button)
        segment_layout.addWidget(self.end_label)
        segment_layout.addStretch()
        segment_layout.addWidget(self.cut_button)
        left_layout.addWidget(segment_controls)

        # Add the left panel to the main layout
        main_layout.addWidget(left_panel, 3) # Give it more space

        # Segment list
        self.segment_list = DeselectableListWidget()
        self.segment_list.setFixedWidth(275) # Set fixed width for segment list
        self.segment_list.setItemDelegate(FontDelegate(font_family="Cascadia Mono")) 
        self.segment_list.setContextMenuPolicy(Qt.CustomContextMenu) # Enable custom context menu
        main_layout.addWidget(self.segment_list)

    def _connect_signals(self):
        self.play_button.clicked.connect(self.toggle_play)

        self.media_player.stateChanged.connect(self.update_media_state)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

        self.position_slider.sliderPressed.connect(self.media_player.pause)
        self.position_slider.sliderMoved.connect(self.set_position)
        # Connect sliderReleased to set_position for final position update (after drag or click)
        self.position_slider.sliderReleased.connect(lambda: self.set_position(self.position_slider.value()))

        self.previous_frame_button.clicked.connect(self.previous_frame)
        self.set_start_button.clicked.connect(self.set_start_time)
        self.next_frame_button.clicked.connect(self.next_frame)
        self.set_end_button.clicked.connect(self.set_end_time)

        self.cut_button.clicked.connect(self.process_cut)
        self.segment_list.itemSelectionChanged.connect(self.on_segment_selection_changed) # Handles single click selection
        self.segment_list.customContextMenuRequested.connect(self.show_segment_context_menu)

    def ms_to_time_str(self, ms):
        time = QTime(0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")

    # Media Player Slots
    def toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def update_media_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def update_position(self, position):
        self.position_slider.setValue(position)
        duration = self.media_player.duration()
        self.time_label.setText(f"{self.ms_to_time_str(position)} / {self.ms_to_time_str(duration)}")
        
        # Update end_label if start_time is set and not in editing mode
        if self.start_time is not None and self.selected_segment_index == -1:
            self.end_label.setText(f"End: {self.ms_to_time_str(position)}")

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)
        position = self.media_player.position()
        self.time_label.setText(f"{self.ms_to_time_str(position)} / {self.ms_to_time_str(duration)}")

    def set_position(self, position):
        # Block signals to prevent update_position from being called while we are setting the position
        self.position_slider.blockSignals(True)
        self.media_player.setPosition(position)
        # Unblock signals after setting the position
        self.position_slider.blockSignals(False)

    def next_frame(self):
        """Advances the video by one frame."""
        self.media_player.pause()
        current_position = self.media_player.position()
        new_position = current_position + self.frame_step_ms
        self.media_player.setPosition(int(new_position))

    def previous_frame(self):
        """Rewinds the video by one frame."""
        self.media_player.pause()
        current_position = self.media_player.position()
        new_position = current_position - self.frame_step_ms
        self.media_player.setPosition(int(max(0, new_position))) # Ensure position doesn't go below 0

    # Segment Handling Slots
    def set_start_time(self):
        new_start_time = self.media_player.position()

        if self.selected_segment_index != -1: # Editing an existing segment
            _, end_time = self.segments[self.selected_segment_index]
            if new_start_time >= end_time:
                QMessageBox.warning(self, "Invalid Time", "Start time must be before the segment's end time.")
                return
            self.segments[self.selected_segment_index] = (new_start_time, end_time)
            self.update_segment_item_text(self.selected_segment_index)
            self.position_slider.set_segment_markers(self.segments)
            self.start_label.setText(f"Start: {self.ms_to_time_str(new_start_time)}")
        else: # Setting start for a new segment
            self.start_time = new_start_time
            self.position_slider.set_current_start_marker(self.start_time)
            self.start_label.setText(f"Start: {self.ms_to_time_str(self.start_time)}")

    def set_end_time(self):
        new_end_time = self.media_player.position()

        if self.selected_segment_index != -1: # Editing an existing segment
            start_time, _ = self.segments[self.selected_segment_index]
            if new_end_time <= start_time:
                QMessageBox.warning(self, "Invalid Time", "End time must be after the segment's start time.")
                return
            self.segments[self.selected_segment_index] = (start_time, new_end_time)
            self.update_segment_item_text(self.selected_segment_index)
            self.position_slider.set_segment_markers(self.segments)
            self.end_label.setText(f"End: {self.ms_to_time_str(new_end_time)}")
            # Deselect to return to "add" mode
            self.segment_list.clearSelection()
            return

        # --- Logic for adding a new segment ---
        current_start_time = self.start_time
        
        if current_start_time is None:
            QMessageBox.warning(self, "Incomplete Segment", "Please set a start time for the new segment first.")
            return

        if current_start_time >= new_end_time:
            QMessageBox.warning(self, "Invalid Segment", "End time must be after start time.")
            return
        
        # Add segment to list
        segment = (current_start_time, new_end_time)
        self.segments.append(segment)
        
        start_str = self.ms_to_time_str(current_start_time)
        end_str = self.ms_to_time_str(new_end_time)
        
        item = QListWidgetItem(f"{start_str} -> {end_str}")
        self.segment_list.addItem(item)

        # Update segment markers and clear temporary start marker
        self.position_slider.set_segment_markers(self.segments)
        self.position_slider.set_current_start_marker(-1)

        # Reset for next segment
        self.start_time = None # Reset start_time after adding segment
        self.start_label.setText("Start: --:--:--")

    def clear_segments(self):
        # This method is no longer connected to a button, but good to keep for internal use
        self.segments.clear()
        self.segment_list.clear()
        self.position_slider.set_segment_markers([])
        self.position_slider.set_current_start_marker(-1)
        self.start_time = None
        self.end_time = None # Ensure end_time is also reset
        self.selected_segment_index = -1 # Reset selected segment index
        self.start_label.setText("Start: --:--:--.---") # Reset label with milliseconds
        self.end_label.setText("End: --:--:--")

    def on_segment_selection_changed(self):
        """Handles selection changes in the segment list."""
        selected_items = self.segment_list.selectedItems()
        if not selected_items:
            # No selection, reset to "add new" mode
            self.selected_segment_index = -1
            self.start_time = None # Clear temporary start time
            self.position_slider.set_current_start_marker(-1) # Clear start marker
            self.start_label.setText("Start: --:--:--.---") # Reset label with milliseconds
            self.end_label.setText("End: --:--:--")
            return

        # An item is selected, enter "edit" mode
        selected_item = selected_items[0]
        self.selected_segment_index = self.segment_list.row(selected_item)
        
        # Safety check to prevent IndexError if lists are out of sync
        if not (0 <= self.selected_segment_index < len(self.segments)):
            self.clear_segments() # Reset state if something is wrong
            return

        start_ms, end_ms = self.segments[self.selected_segment_index]
        self.media_player.setPosition(start_ms)
        self.media_player.pause()

        self.start_label.setText(f"Start: {self.ms_to_time_str(start_ms)}")
        self.end_label.setText(f"End: {self.ms_to_time_str(end_ms)}")

    def update_segment_item_text(self, row):
        start_ms, end_ms = self.segments[row]
        self.segment_list.item(row).setText(f"{self.ms_to_time_str(start_ms)} -> {self.ms_to_time_str(end_ms)}")

    def update_all_segment_item_texts(self):
        """Updates the text for all segment items in the list, re-numbering them."""
        for i in range(len(self.segments)):
            start_ms, end_ms = self.segments[i]
            self.segment_list.item(i).setText(f"{self.ms_to_time_str(start_ms)} -> {self.ms_to_time_str(end_ms)}")

    def show_segment_context_menu(self, pos: QPoint):
        """Displays a context menu for segments in the list."""
        item = self.segment_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit Segment")
        delete_action = menu.addAction("Delete Segment")

        action = menu.exec_(self.segment_list.mapToGlobal(pos))

        if action == edit_action:
            self.edit_segment_from_context_menu(item)
        elif action == delete_action:
            self.delete_segment_from_context_menu(item)

    def edit_segment_from_context_menu(self, item: QListWidgetItem):
        """Selects the given segment item, triggering the edit mode."""
        row = self.segment_list.row(item)
        if not (0 <= row < len(self.segments)):
            return # Should not happen if item is valid

        initial_start_ms, initial_end_ms = self.segments[row]

        dialog = EditSegmentDialog(self, initial_start_ms, initial_end_ms)
        if dialog.exec_() == QDialog.Accepted:
            new_start_ms, new_end_ms = dialog.get_edited_times()
            
            self.segments[row] = (new_start_ms, new_end_ms)
            self.update_segment_item_text(row)
            self.position_slider.set_segment_markers(self.segments)
            
            # Re-select the item to update labels and seek to its start
            self.segment_list.setCurrentItem(item)

    def delete_segment_from_context_menu(self, item: QListWidgetItem):
        """Deletes the selected segment from the list and updates UI."""
        row_to_delete = self.segment_list.row(item)
        if row_to_delete < 0:
            return

        # Remove segment without confirmation
        self.segments.pop(row_to_delete)
        self.segment_list.takeItem(row_to_delete) # Removes item from QListWidget
        self.position_slider.set_segment_markers(self.segments)
        self.update_all_segment_item_texts() # Re-number remaining segments

        # Adjust selected_segment_index if necessary
        if self.selected_segment_index == row_to_delete:
            self.segment_list.clearSelection() # This will reset selected_segment_index and labels
        elif self.selected_segment_index > row_to_delete:
            self.selected_segment_index -= 1

    # Processing Slots
    def process_cut(self):
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Please add at least one segment to cut.")
            return

        output_dir = self.output_path
        base_name, ext = os.path.splitext(os.path.basename(self.video_path))

        for i, (start_ms, end_ms) in enumerate(self.segments):
            start_str = self.ms_to_time_str(start_ms)
            end_str = self.ms_to_time_str(end_ms)
            # Sanitize filename parts by replacing ':' with '-'
            safe_start_str = start_str.replace(':', '-')
            safe_end_str = end_str.replace(':', '-')
            output_file = os.path.join(output_dir, f"{safe_start_str}--{safe_end_str}--{base_name}{ext}")
            
            command = f'ffmpeg -loglevel warning -i "{self.video_path}" -ss {start_str} -to {end_str} -c copy "{output_file}"'
            
            # Create and run a worker for each segment
            worker = FFmpegWorker(
                selected_files=[],
                command_input=None, # Not needed for command_override
                output_path=None,   # Not needed for command_override
                command_override=command
            )
            worker.log_signal.connect(self.logger.append_log)
            worker.finished.connect(lambda w=worker: self.active_workers.remove(w))
            self.active_workers.append(worker)
            worker.start()
        
        self.logger.append_log(f"INFO: {len(self.segments)} cut operations have been started.")
        
        # Clear segments after processing to allow for new cuts
        self.segments.clear()
        self.segment_list.clear()
        self.position_slider.set_segment_markers([]) # Clear all markers
        self.start_time = None
        self.end_time = None
        self.start_label.setText("Start: --:--:--.---") # Reset label with milliseconds
        self.end_label.setText("End: --:--:--")

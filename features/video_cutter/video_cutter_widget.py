import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
                             QListWidgetItem, QMenu)
from PyQt5.QtCore import Qt, QUrl, QTime, QPoint
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from processor import FFmpegWorker
from components import FontDelegate
from .components.media_controls import MediaControls
from .components.segment_controls import SegmentControls
from .components.segment_list import SegmentList
from .components.clickable_video_widget import ClickableVideoWidget
from .components.edit_segment_dialog import EditSegmentDialog

class VideoCutterWidget(QDialog):

    def __init__(self, video_path, output_path, logger, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cutter")
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
        self.frame_step_ms = 33  # Step for ~30fps
        self.selected_segment_index = -1  # -1 means no segment is selected for editing

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        if not self._media_loaded:
            if os.path.exists(self.video_path):
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_path)))
                self.media_controls.play_button.setEnabled(True)
                self._media_loaded = True
                self.media_player.play()
            else:
                QMessageBox.critical(self, "Error", f"Video file not found:\n{self.video_path}")
                self.media_controls.play_button.setEnabled(False)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player and release resources."""
        self.media_player.stop()
        super().closeEvent(event)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel for video and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Video display
        self.video_widget = ClickableVideoWidget()
        self.video_widget.setMinimumHeight(300)
        left_layout.addWidget(self.video_widget, 1) # Give it expanding space

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # Media and Segment Controls
        self.media_controls = MediaControls()
        self.segment_controls = SegmentControls()

        left_layout.addWidget(self.media_controls)
        left_layout.addWidget(self.segment_controls)

        # Add the left panel to the main layout
        main_layout.addWidget(left_panel, 3)  # Give it more space

        # Segment list
        self.segment_list_widget = SegmentList()
        self.segment_list_widget.setItemDelegate(FontDelegate(font_family="Cascadia Mono"))
        main_layout.addWidget(self.segment_list_widget)

    def _connect_signals(self):
        # --- Media Player and Controls ---
        self.media_controls.play_button.clicked.connect(self.toggle_play)
        self.video_widget.doubleClicked.connect(self.toggle_play)
        self.media_controls.previous_frame_button.clicked.connect(self.previous_frame)
        self.media_controls.next_frame_button.clicked.connect(self.next_frame)
        self.media_controls.position_slider.sliderPressed.connect(self.media_player.pause)
        self.media_controls.position_slider.valueChanged.connect(self.set_position)

        self.media_player.stateChanged.connect(self.media_controls.update_media_state)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

        # --- Segment Controls and List ---
        self.segment_controls.set_start_button.clicked.connect(self.set_start_time)
        self.segment_controls.set_end_button.clicked.connect(self.set_end_time)
        self.segment_controls.cut_button.clicked.connect(self.process_cut)

        self.segment_list_widget.itemSelectionChanged.connect(self.on_segment_selection_changed)
        self.segment_list_widget.customContextMenuRequested.connect(self.show_segment_context_menu)

    def ms_to_time_str(self, ms):
        time = QTime(0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")

    # --- Media Player Slots ---
    def toggle_play(self):
        if self.media_player.position() >= self.media_player.duration() - 100:
            self.media_player.setPosition(0)
            self.media_player.play()
        elif self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def update_position(self, position):
        self.media_controls.update_position(position, self.media_player.duration())
        if self.start_time is not None and self.selected_segment_index == -1:
            self.segment_controls.end_label.setText(f"End: {self.ms_to_time_str(position)}")

    def update_duration(self, duration):
        self.media_controls.update_duration(duration, self.media_player.position())

    def set_position(self, position):
        if self.media_player.position() != position:
            self.media_player.setPosition(position)

    def next_frame(self):
        self.media_player.pause()
        current_position = self.media_player.position()
        new_position = current_position + self.frame_step_ms
        self.media_player.setPosition(int(new_position))

    def previous_frame(self):
        self.media_player.pause()
        current_position = self.media_player.position()
        new_position = current_position - self.frame_step_ms
        self.media_player.setPosition(int(max(0, new_position)))

    # --- Segment Handling Slots ---
    def set_start_time(self):
        new_start_time = self.media_player.position()

        if self.selected_segment_index != -1:  # Editing an existing segment
            _, end_time = self.segments[self.selected_segment_index]
            if new_start_time >= end_time:
                QMessageBox.warning(self, "Invalid Time", "Start time must be before the segment's end time.")
                return
            self.segments[self.selected_segment_index] = (new_start_time, end_time)
            self.update_segment_item_text(self.selected_segment_index)
            self.media_controls.position_slider.set_segment_markers(self.segments)
            self.segment_controls.start_label.setText(f"Start: {self.ms_to_time_str(new_start_time)}")
        else:  # Setting start for a new segment
            self.start_time = new_start_time
            self.media_controls.position_slider.set_current_start_marker(self.start_time)
            self.segment_controls.start_label.setText(f"Start: {self.ms_to_time_str(self.start_time)}")

    def set_end_time(self):
        new_end_time = self.media_player.position()

        if self.selected_segment_index != -1:  # Editing an existing segment
            start_time, _ = self.segments[self.selected_segment_index]
            if new_end_time <= start_time:
                QMessageBox.warning(self, "Invalid Time", "End time must be after the segment's start time.")
                return
            self.segments[self.selected_segment_index] = (start_time, new_end_time)
            self.update_segment_item_text(self.selected_segment_index)
            self.media_controls.position_slider.set_segment_markers(self.segments)
            self.segment_controls.end_label.setText(f"End: {self.ms_to_time_str(new_end_time)}")
            self.segment_list_widget.clearSelection()
            return

        # --- Logic for adding a new segment ---
        if self.start_time is None:
            QMessageBox.warning(self, "Incomplete Segment", "Please set a start time for the new segment first.")
            return

        if self.start_time >= new_end_time:
            QMessageBox.warning(self, "Invalid Segment", "End time must be after start time.")
            return

        segment = (self.start_time, new_end_time)
        self.segments.append(segment)

        item_text = f"{self.ms_to_time_str(self.start_time)} -> {self.ms_to_time_str(new_end_time)}"
        self.segment_list_widget.addItem(QListWidgetItem(item_text))

        self.media_controls.position_slider.set_segment_markers(self.segments)
        self.media_controls.position_slider.set_current_start_marker(-1)

        self.start_time = None
        self.segment_controls.reset_labels()

    def clear_segments_ui(self):
        self.segments.clear()
        self.segment_list_widget.clear()
        self.media_controls.position_slider.set_segment_markers([])
        self.media_controls.position_slider.set_current_start_marker(-1)
        self.start_time = None
        self.end_time = None
        self.selected_segment_index = -1
        self.segment_controls.reset_labels()

    def on_segment_selection_changed(self):
        selected_items = self.segment_list_widget.selectedItems()
        if not selected_items:
            self.selected_segment_index = -1
            self.start_time = None
            self.media_controls.position_slider.set_current_start_marker(-1)
            self.segment_controls.reset_labels()
            return

        selected_item = selected_items[0]
        self.selected_segment_index = self.segment_list_widget.row(selected_item)

        if not (0 <= self.selected_segment_index < len(self.segments)):
            self.clear_segments_ui()
            return

        start_ms, end_ms = self.segments[self.selected_segment_index]
        self.media_player.setPosition(start_ms)
        self.media_player.pause()

        self.segment_controls.start_label.setText(f"Start: {self.ms_to_time_str(start_ms)}")
        self.segment_controls.end_label.setText(f"End: {self.ms_to_time_str(end_ms)}")

    def update_segment_item_text(self, row):
        start_ms, end_ms = self.segments[row]
        item_text = f"{self.ms_to_time_str(start_ms)} -> {self.ms_to_time_str(end_ms)}"
        self.segment_list_widget.item(row).setText(item_text)

    def update_all_segment_item_texts(self):
        for i in range(len(self.segments)):
            self.update_segment_item_text(i)

    def show_segment_context_menu(self, pos: QPoint):
        item = self.segment_list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit Segment")
        delete_action = menu.addAction("Delete Segment")

        action = menu.exec_(self.segment_list_widget.mapToGlobal(pos))

        if action == edit_action:
            self.edit_segment_from_context_menu(item)
        elif action == delete_action:
            self.delete_segment_from_context_menu(item)

    def edit_segment_from_context_menu(self, item: QListWidgetItem):
        row = self.segment_list_widget.row(item)
        if not (0 <= row < len(self.segments)):
            return

        initial_start_ms, initial_end_ms = self.segments[row]

        dialog = EditSegmentDialog(self, initial_start_ms, initial_end_ms)
        if dialog.exec_() == QDialog.Accepted:
            new_start_ms, new_end_ms = dialog.get_edited_times()

            self.segments[row] = (new_start_ms, new_end_ms)
            self.update_segment_item_text(row)
            self.media_controls.position_slider.set_segment_markers(self.segments)
            self.segment_list_widget.setCurrentItem(item)

    def delete_segment_from_context_menu(self, item: QListWidgetItem):
        row_to_delete = self.segment_list_widget.row(item)
        if row_to_delete < 0:
            return

        self.segments.pop(row_to_delete)
        self.segment_list_widget.takeItem(row_to_delete)
        self.media_controls.position_slider.set_segment_markers(self.segments)
        self.update_all_segment_item_texts()

        if self.selected_segment_index == row_to_delete:
            self.segment_list_widget.clearSelection()
        elif self.selected_segment_index > row_to_delete:
            self.selected_segment_index -= 1

    # --- Processing Slots ---
    def process_cut(self):
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Please add at least one segment to cut.")
            return

        output_dir = self.output_path
        base_name, ext = os.path.splitext(os.path.basename(self.video_path))

        for i, (start_ms, end_ms) in enumerate(self.segments):
            start_str = self.ms_to_time_str(start_ms)
            end_str = self.ms_to_time_str(end_ms)

            safe_start_str = start_str.replace(':', '-')
            safe_end_str = end_str.replace(':', '-')
            output_file = os.path.join(output_dir, f"{safe_start_str}--{safe_end_str}--{base_name}{ext}")

            command = f'ffmpeg -loglevel warning -ss {start_str} -to {end_str} -i "{self.video_path}" -c copy "{output_file}"'

            worker = FFmpegWorker(
                selected_files=[],
                command_input=None,
                output_path=None,
                command_override=command
            )
            worker.log_signal.connect(self.logger.append_log)
            worker.finished.connect(lambda w=worker: self.active_workers.remove(w))
            self.active_workers.append(worker)
            worker.start()

        self.logger.append_log(f"INFO: {len(self.segments)} cut operations have been started.")
        self.clear_segments_ui()
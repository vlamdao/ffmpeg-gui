import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
                             QListWidgetItem, QMenu)
from PyQt5.QtCore import Qt, QUrl, QTime, QPoint
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtGui import QFont

from processor import FFmpegWorker
from helper import FontDelegate, ms_to_time_str

from .components import (MediaControls, MediaPlayer, SegmentControls, 
                         SegmentList, SegmentManager
)
class VideoCutter(QDialog):

    def __init__(self, video_path, output_path, logger, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cutter")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(1200, 600)

        # Dependencies
        self.video_path = video_path
        self.logger = logger
        self.output_path = output_path

        # Logic and State Management
        self.active_workers = []

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self.media_player_widget.load_media(self.video_path)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player and release resources."""
        self.media_player_widget.stop()
        super().closeEvent(event)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel for video and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Media Player, Media Controls, and Segment Controls
        self.segment_manager = SegmentManager(self)
        self.media_player_widget = MediaPlayer()
        left_layout.addWidget(self.media_player_widget)
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
        self.media_controls.play_button.clicked.connect(self.media_player_widget.toggle_play)
        self.media_controls.previous_frame_button.clicked.connect(self.media_player_widget.previous_frame)
        self.media_controls.next_frame_button.clicked.connect(self.media_player_widget.next_frame)
        self.media_controls.position_slider.sliderPressed.connect(self.media_player_widget.pause)
        self.media_controls.position_slider.valueChanged.connect(self.media_player_widget.set_position)

        self.media_player_widget.media_loaded.connect(self.media_controls.play_button.setEnabled)
        self.media_player_widget.state_changed.connect(self.media_controls.update_media_state)
        self.media_player_widget.position_changed.connect(self.update_position)
        self.media_player_widget.duration_changed.connect(self.media_controls.update_duration)
        self.media_player_widget.double_clicked.connect(self.media_player_widget.toggle_play)

        # --- Segment Controls and List ---
        self.segment_controls.set_start_button.clicked.connect(lambda: self.segment_manager.set_start_time(self.media_player_widget.position()))
        self.segment_controls.set_end_button.clicked.connect(lambda: self.segment_manager.set_end_time(self.media_player_widget.position()))
        self.segment_controls.cut_button.clicked.connect(self.process_cut)

        self.segment_list_widget.itemSelectionChanged.connect(self.on_segment_selection_changed)
        self.segment_list_widget.customContextMenuRequested.connect(self.show_segment_context_menu)

        # --- Connect Segment Manager to UI Components ---
        self.segment_manager.segments_updated.connect(self.media_controls.position_slider.set_segment_markers)
        self.segment_manager.current_start_marker_updated.connect(self.media_controls.position_slider.set_current_start_marker)
        self.segment_manager.labels_updated.connect(self.update_segment_labels)
        self.segment_manager.list_item_added.connect(self.segment_list_widget.addItem)
        self.segment_manager.list_item_updated.connect(lambda index, text: self.segment_list_widget.item(index).setText(text))
        self.segment_manager.list_item_removed.connect(self.segment_list_widget.takeItem)
        self.segment_manager.list_selection_cleared.connect(self.segment_list_widget.clearSelection)
        self.segment_manager.list_cleared.connect(self.segment_list_widget.clear)

    # --- Media Player Slots ---
    def update_position(self, position):
        # Update media controls UI
        self.media_controls.update_position(position, self.media_player_widget.duration())
        # Update segment controls UI (business logic)
        self.segment_manager.update_dynamic_end_label(position)

    # --- Segment Manager Slots ---
    def update_segment_labels(self, updates):
        if updates.get('reset'):
            self.segment_controls.reset_labels()
            return
        if 'start' in updates:
            self.segment_controls.update_start_label(updates['start'])
        if 'end' in updates:
            self.segment_controls.update_end_label(updates['end'])

    # --- UI Event Handlers ---
    def on_segment_selection_changed(self):
        selected_items = self.segment_list_widget.selectedItems()
        selected_row = self.segment_list_widget.row(selected_items[0]) if selected_items else -1
        start_pos, _ = self.segment_manager.handle_selection_change(selected_row)
        if start_pos != -1:
            self.media_player_widget.set_position(start_pos)
            self.media_player_widget.pause()

    def show_segment_context_menu(self, pos: QPoint):
        item = self.segment_list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit Segment")
        delete_action = menu.addAction("Delete Segment")

        action = menu.exec_(self.segment_list_widget.mapToGlobal(pos))

        if action == edit_action:
            row_to_select = self.segment_manager.edit_segment(self.segment_list_widget.row(item))
            if row_to_select != -1:
                self.segment_list_widget.setCurrentRow(row_to_select)
        elif action == delete_action:
            self.segment_manager.delete_segment(self.segment_list_widget.row(item))

    # --- Processing Slots ---
    def process_cut(self):
        segments_to_process = self.segment_manager.get_segments_for_processing()
        if not segments_to_process: return

        output_dir = self.output_path
        base_name, ext = os.path.splitext(os.path.basename(self.video_path))

        for start_ms, end_ms in segments_to_process:
            start_str = ms_to_time_str(start_ms)
            end_str = ms_to_time_str(end_ms)

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

        self.logger.append_log(f"INFO: {len(segments_to_process)} cut operations have been started.")
        self.segment_manager.clear_all()
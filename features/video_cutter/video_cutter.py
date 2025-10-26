import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
                             QMenu)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtGui import QFont

from processor import FFmpegWorker
from helper import FontDelegate, ms_to_time_str

from .components import (MediaControls, MediaPlayer, SegmentControls, 
                         SegmentList, SegmentManager)
class VideoCutter(QDialog):
    """A dialog for cutting segments from a video file.

    This class acts as the main controller for the video cutting feature. It
    assembles all the necessary UI components (player, controls, segment list)
    and wires them together, orchestrating the interactions between them.
    """
    _LEFT_PANEL_STRETCH = 3

    def __init__(self, video_path, output_path, logger, parent=None):
        """Initializes the VideoCutter dialog.

        Args:
            video_path (str): The absolute path to the video file to be loaded.
            output_path (str): The directory where cut segments will be saved.
            logger (Logger): An instance of the logger for displaying messages.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Video Cutter")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(1200, 600)

        # Dependencies
        self._video_path = video_path
        self._logger = logger
        self._output_path = output_path

        # Logic and State Management
        self._active_workers = []

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self._media_player.load_media(self._video_path)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player and any active workers."""
        self._media_player.stop()
        # Terminate any running FFmpeg processes to prevent orphaned processes.
        for worker in self._active_workers:
            if worker.isRunning():
                worker.terminate()
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
        self._segment_manager = SegmentManager(self)

        self._media_player = MediaPlayer()
        left_layout.addWidget(self._media_player)
        self._media_controls = MediaControls()
        self._segment_controls = SegmentControls()

        left_layout.addWidget(self._media_controls)
        left_layout.addWidget(self._segment_controls)

        # Add the left panel to the main layout
        main_layout.addWidget(left_panel, self._LEFT_PANEL_STRETCH)

        # Segment list
        self._segment_list = SegmentList()
        self._segment_list.setItemDelegate(FontDelegate(font_family="Consolas"))
        main_layout.addWidget(self._segment_list)

    def _connect_signals(self):
        """Connects signals and slots between all the components."""
        # --- Media Player and Controls ---
        self._media_controls.play_clicked.connect(self._media_player.toggle_play)
        self._media_controls.seek_backward_clicked.connect(self._media_player.seek_backward)
        self._media_controls.seek_forward_clicked.connect(self._media_player.seek_forward)
        self._media_controls.slider_pressed.connect(self._media_player.pause)
        self._media_controls.position_changed.connect(self._media_player.set_position)

        self._media_player.media_loaded.connect(self._media_controls.set_play_button_enabled)
        self._media_player.state_changed.connect(self._media_controls.update_media_state)
        self._media_player.position_changed.connect(self._update_position)
        self._media_player.duration_changed.connect(self._update_duration)
        self._media_player.double_clicked.connect(self._media_player.toggle_play)

        # --- Segment Controls and List ---
        self._segment_controls.set_start_clicked.connect(lambda: self._segment_manager.set_start_time(self._media_player.position()))
        self._segment_controls.set_end_clicked.connect(lambda: self._segment_manager.create_segment(self._media_player.position()))
        self._segment_controls.cut_clicked.connect(self._process_cut)
        self._segment_controls.close_clicked.connect(self.close)

        self._segment_list.itemSelectionChanged.connect(self._on_segment_selection_changed)
        self._segment_list.customContextMenuRequested.connect(self._show_segment_context_menu)

        # --- Connect Segment Manager to UI Components ---
        self._segment_manager.error_occurred.connect(self._show_error_message)
        self._segment_manager.segments_updated.connect(self._media_controls.set_segment_markers)
        self._segment_manager.current_start_marker_updated.connect(self._media_controls.set_current_start_marker)
        
        # Connect manager to list widget
        self._segment_manager.segment_added.connect(self._segment_list.add_segment)
        self._segment_manager.segment_updated.connect(self._segment_list.update_segment)
        self._segment_manager.segment_removed.connect(self._segment_list.takeItem)
        self._segment_manager.list_cleared.connect(self._segment_list.clear)
        self._segment_manager.selection_cleared.connect(self._segment_list.clearSelection)

    # --- Media Player Slots ---
    def _update_position(self, position):
        """Slot to handle the player's positionChanged signal.

        Forwards the position to the media controls for UI updates and to the
        segment manager for live end-time previews.
        """
        self._media_controls.update_position(position, self._media_player.duration())

    def _update_duration(self, duration):
        """Slot to handle the player's durationChanged signal."""
        self._media_controls.update_duration(duration)
        self._media_controls.update_position(self._media_player.position(), duration)

    def _show_error_message(self, title: str, message: str) -> None:
        """Displays a warning message box."""
        QMessageBox.warning(self, title, message)

    # --- UI Event Handlers ---
    def _on_segment_selection_changed(self):
        """Handles selection changes in the segment list."""
        selected_items = self._segment_list.selectedItems()
        
        # Check if there are any selected items before trying to access them.
        # This prevents a crash when an item is deleted, which can trigger
        # this slot with an empty selection.
        selected_row = self._segment_list.row(selected_items[0]) if selected_items else -1

        start_pos, _ = self._segment_manager.handle_selection_change(selected_row)
        if start_pos != -1:
            self._media_player.set_position(start_pos)
            self._media_player.pause()

    def _show_segment_context_menu(self, pos: QPoint):
        """Shows a context menu for a segment item (Edit, Delete)."""
        # Get the index of the item at the cursor position.
        # Working with the row index is safer than holding a reference to the item,
        # which might be deleted, causing a crash.
        row = self._segment_list.row(self._segment_list.itemAt(pos))
        if row == -1:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit Segment")
        delete_action = menu.addAction("Delete Segment")

        action = menu.exec_(self._segment_list.viewport().mapToGlobal(pos))

        if action == edit_action:
            row_to_select = self._segment_manager.edit_segment(row)
            if row_to_select != -1:
                self._segment_list.setCurrentRow(row_to_select)
        elif action == delete_action:
            self._segment_manager.delete_segment(row)

    # --- Processing Slots ---
    def _process_cut(self):
        """Initiates the cutting process for all defined segments."""
        segments_to_process = self._segment_manager.get_segments_for_processing()
        if not segments_to_process: return

        output_dir = self._output_path
        base_name, ext = os.path.splitext(os.path.basename(self._video_path))

        for start_ms, end_ms in segments_to_process:
            self._start_cut_worker(start_ms, end_ms, base_name, ext, output_dir)

        self._logger.append_log(f"INFO: {len(segments_to_process)} cut operations have been started.")
        self._segment_manager.clear_all()

    def _start_cut_worker(self, start_ms: int, end_ms: int, base_name: str, ext: str, output_dir: str):
        """Creates and starts an FFmpegWorker for a single segment."""
        start_str = ms_to_time_str(start_ms)
        end_str = ms_to_time_str(end_ms)

        # Create a filesystem-safe filename from the timestamps
        safe_start_str = start_str.replace(':', '-').replace('.', '_')
        safe_end_str = end_str.replace(':', '-').replace('.', '_')
        output_file = os.path.join(output_dir, f"{base_name}--{safe_start_str}--{safe_end_str}{ext}")

        command = f'ffmpeg -loglevel warning -ss {start_str} -to {end_str} -i "{self._video_path}" -c copy "{output_file}"'

        worker = FFmpegWorker(
            selected_files=[],
            command_input=None,
            output_path=None,
            command_override=command
        )
        worker.log_signal.connect(self._logger.append_log)
        worker.finished.connect(lambda w=worker: self._active_workers.remove(w))
        self._active_workers.append(worker)
        worker.start()
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
                             QMenu)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor

from .components import (MediaControls, MediaPlayer, SegmentControls, 
                         SegmentList, SegmentManager, EditSegmentDialog)
from .components import CommandTemplate
from .processor import SegmentProcessor
from helper import FontDelegate

class VideoCutter(QDialog):
    """A dialog for cutting segments from a video file.

    This class acts as the main controller for the video cutting feature. It
    assembles all the necessary UI components (player, controls, segment list)
    and wires them together, orchestrating the interactions between them.
    """
    _LEFT_PANEL_STRETCH = 3
    _PROCESSING_COLOR = QColor("#5cce77")  # A light green color
    _PENDING_COLOR = QColor("#ffe58e")  # A light yellow color


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
        self.setMinimumSize(1200, 750)

        # Dependencies
        self._video_path = video_path
        self._logger = logger
        self._output_folder = output_path

        # Logic and State Management
        self._segment_processor = None # Will be initialized in _setup_ui

        self._setup_ui()
        self._connect_signals()

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self._media_player.load_media(self._video_path)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player and any active workers."""
        self._media_player.stop()
        if self._segment_processor:
            # Terminate any running FFmpeg processes to prevent orphaned processes.
            for worker in self._segment_processor.get_active_workers():
                if worker.isRunning():
                    worker.terminate()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Handle key presses for the dialog."""
        if event.key() == Qt.Key_Escape:
            if not self._segment_manager.cancel_creation():
                super().keyPressEvent(event) # Allow default Esc behavior (close dialog)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self._segment_manager = SegmentManager(self)

        # Left panel for video and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._media_player = MediaPlayer()
        self._media_controls = MediaControls()
        self._segment_controls = SegmentControls()
        self._command_template = CommandTemplate(
            video_path=self._video_path,
            output_path=self._output_folder,
            parent=self
        )

        # Create a container for the bottom controls (media control + segment + command)
        bottom_controls = QWidget()
        bottom_layout = QVBoxLayout(bottom_controls)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)
        bottom_layout.addWidget(self._media_controls)
        bottom_layout.addWidget(self._segment_controls)
        bottom_layout.addWidget(self._command_template)

        left_layout.addWidget(self._media_player, 1)
        left_layout.addWidget(bottom_controls)

        self._segment_list = SegmentList()
        self._segment_list.setItemDelegate(FontDelegate(font_family="Consolas"))
        
        main_layout.addWidget(left_panel, self._LEFT_PANEL_STRETCH)
        main_layout.addWidget(self._segment_list)

        self._segment_processor = SegmentProcessor(
            logger=self._logger,
            parent=self
        )

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
        self._media_player.position_changed.connect(self._on_position_changed)
        self._media_player.duration_changed.connect(self._on_duration_changed)
        self._media_player.double_clicked.connect(self._media_player.toggle_play)

        # --- Segment Controls and List ---
        self._segment_controls.set_start_clicked.connect(self._on_set_start_time)
        self._segment_controls.set_end_clicked.connect(self._on_set_end_time)
        self._segment_controls.stop_clicked.connect(self._segment_processor.stop_processing)
        self._segment_controls.cut_clicked.connect(self._on_cut_clicked)

        self._segment_list.itemSelectionChanged.connect(self._on_segment_selected)
        self._segment_list.customContextMenuRequested.connect(self._show_segment_context_menu)

        # --- Connect Segment Manager to UI Components ---
        self._segment_manager.error_occurred.connect(self._show_error_message)
        self._segment_manager.segments_updated.connect(self._media_controls.set_segment_markers)
        self._segment_manager.start_marker_updated.connect(self._media_controls.set_current_start_marker)
        
        # Connect manager to list widget
        self._segment_manager.segment_added.connect(self._segment_list.add_segment)
        self._segment_manager.segment_updated.connect(self._segment_list.update_segment)
        self._segment_manager.segment_removed.connect(self._segment_list.takeItem)
        self._segment_manager.selection_cleared.connect(self._segment_list.clearSelection)

        # --- Connect Segment Processor to UI ---
        self._segment_processor.processing_started.connect(self._on_processing_started)
        self._segment_processor.processing_stopped.connect(self._on_processing_stopped)
        self._segment_processor.segment_processing.connect(self._on_segment_processing)
        self._segment_processor.segment_processed.connect(self._segment_manager.delete_segment_by_data)


    def _show_error_message(self, title: str, message: str) -> None:
        """Displays a warning message box."""
        QMessageBox.warning(self, title, message)

    # ==================================================================
    # Media Player Slots
    # ==================================================================
    def _on_duration_changed(self, duration):
        """Slot to handle the player's durationChanged signal.
            This event is only emitted once when the media is loaded.
            When media is loaded, update the duration in the media controls.
            And update the position to 0.
        """
        self._media_controls.update_duration(duration)
        self._media_controls.update_position(self._media_player.position(), duration)

    def _on_position_changed(self, position):
        """Slot to handle the player's positionChanged signal."""
        self._media_controls.update_position(position, self._media_player.duration())

    # ==================================================================
    # Segment Manager Slots
    # ==================================================================
    def _on_set_start_time(self):
        """Handles the event when the start time button is clicked."""
        self._segment_manager.set_start_time(self._media_player.position())
    
    def _on_set_end_time(self):
        """Handles the event when the end time button is clicked."""
        self._segment_manager.set_end_time(self._media_player.position())

    # ==================================================================
    # Processor Slots
    # ==================================================================
    def _set_ui_processing_state(self, is_processing: bool):
        """Enables or disables UI components based on processing state."""
        self._media_controls.setEnabled(not is_processing)
        self._segment_list.setEnabled(not is_processing)
        self._command_template.setEnabled(not is_processing)
        self._segment_controls.set_processing_state(is_processing)

    def _on_processing_started(self, total_segments: int):
        """Handles the start of the segment processing task."""
        self._set_ui_processing_state(True)
        for i in range(total_segments):
            self._segment_list.highlight_row(i, self._PENDING_COLOR)

    def _on_processing_stopped(self):
        """Handles the end of the segment processing task."""
        self._set_ui_processing_state(False)
        self._segment_list.clear_highlights()

    def _on_segment_processing(self, segment_data: tuple[int, int]):
        row = self._segment_list.find_segment_by_data(segment_data)
        if row != -1:
            self._segment_list.highlight_row(row, self._PROCESSING_COLOR)
        else:
            self._logger.append_log(f"Warning: Could not find segment {segment_data} in the list to highlight.")

    def _on_cut_clicked(self):
        segments = self._segment_manager.get_segments_for_processing()
        if not segments:
            return

        jobs = []
        for start_ms, end_ms in segments:
            command = self._command_template.generate_command(start_ms, end_ms)
            if not command:
                self._show_error_message("Command Error", "Could not generate command. Check the command template.")
                return # Stop if any command fails to generate
            jobs.append(((start_ms, end_ms), command))
        self._segment_processor.start_processing(jobs)

    # ==================================================================
    # Segment List Slots
    # ==================================================================
    def _on_segment_selected(self):
        """Handles selection changes in the segment list."""
        selected_items = self._segment_list.selectedItems()
        if selected_items:
            segment_index = self._segment_list.row(selected_items[0])
        else:
            segment_index = -1
        
        # First, notify the manager of the selection change to update its state.
        self._segment_manager.handle_segment_selection(segment_index)
        # get selected segment and seek to its start time
        selected_segment = self._segment_manager.get_segment_at(segment_index)
        if selected_segment:
            self._media_player.set_position(selected_segment[0])
            self._media_player.pause()

    def _show_segment_context_menu(self, pos: QPoint):
        """Shows a context menu for a segment item (Edit, Delete)."""
        row = self._segment_list.row(self._segment_list.itemAt(pos))
        if row == -1:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit Segment")
        delete_action = menu.addAction("Delete Segment")

        action = menu.exec_(self._segment_list.viewport().mapToGlobal(pos))

        if action == edit_action:
            self._edit_segment(row)
        elif action == delete_action:
            self._segment_manager.delete_segment(row)

    def _edit_segment(self, row: int):
        """Handles the logic for editing a segment via a dialog."""
        segment = self._segment_manager.get_segment_at(row)
        if not segment:
            return

        start_ms, end_ms = segment
        dialog = EditSegmentDialog(self, start_ms, end_ms)

        if dialog.exec_() == QDialog.Accepted:
            new_start, new_end = dialog.get_edited_times()
            if self._segment_manager.update_segment(row, new_start, new_end):
                self._segment_list.setCurrentRow(row)
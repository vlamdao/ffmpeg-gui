from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QMessageBox, QMenu
                             )
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QIcon

from components import PlaceholdersTable
from features.player import ControlledPlayer, MarkerSlider
from .components import (SegmentList,
                         SegmentManager, EditSegmentDialog,
                         CommandTemplate, VideoCutterPlaceholders, ActionPanel
                         )
from .processor import Processor
from helper import styled_text, ms_to_time_str, resource_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components import Logger

class VideoCutter(QDialog):

    _PROCESSING_COLOR = QColor("#5cce77")  # A light green color
    _PENDING_COLOR = QColor("#ffe58e")  # A light yellow color

    def __init__(self, input_file, output_folder, logger: 'Logger', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Cutter")
        self.setWindowIcon(QIcon(resource_path("icon/cut-video.png")))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setMinimumSize(1200, 750)

        self._input_file = input_file
        self._logger = logger
        self._output_folder = output_folder

        self._setup_ui()
        self._connect_signals()
        self._update_ui_state('enable')

    def showEvent(self, event):
        """Override showEvent to load media only when the dialog is shown."""
        super().showEvent(event)
        self._controlled_player.load_media(self._input_file)

    def closeEvent(self, event):
        """Override closeEvent to stop the media player and any active workers."""
        self._controlled_player.cleanup()
        if self._processor and (self._processor.get_active_workers() or self._processor._processing_queue):
            self._processor.stop()
            self._processor.wait()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Handle key presses for the dialog."""
        if event.key() == Qt.Key_Escape:
            if not self._segment_manager.cancel_creation():
                super().keyPressEvent(event)

    def _setup_ui(self):
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        self._segment_manager = SegmentManager(self)
        self._controlled_player = ControlledPlayer(slider_class=MarkerSlider)
        self._action_panel = ActionPanel()

        self._placeholders = VideoCutterPlaceholders()
        self._placeholders_table = PlaceholdersTable(placeholders_list=self._placeholders.get_placeholders_list(),
                                                     num_columns=6,
                                                     parent=self
                                                     )
        self._placeholders_table.set_compact_height()

        self._cmd_template = CommandTemplate(placeholders=self._placeholders, parent=self)
        self._segment_list = SegmentList()
        self._processor = Processor(self)

        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_template.insert_placeholder)
        
    def _setup_layout(self):
        """Configures the layout and adds widgets to it."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(self._controlled_player, 1)
        left_layout.addWidget(self._action_panel)
        left_layout.addWidget(self._placeholders_table)
        left_layout.addWidget(self._cmd_template)

        main_layout.addLayout(left_layout)
        main_layout.addWidget(self._segment_list)

    def _connect_signals(self):
        """Connects signals and slots between all the components."""
        self._action_panel.set_start_clicked.connect(self._on_set_start_time)
        self._action_panel.set_end_clicked.connect(self._on_set_end_time)
        self._action_panel.run_clicked.connect(self._on_cut_clicked)
        self._action_panel.stop_clicked.connect(self._processor.stop)

        self._segment_list.itemSelectionChanged.connect(self._on_segment_selected)
        self._segment_list.customContextMenuRequested.connect(self._show_segment_context_menu)

        self._segment_manager.error_occurred.connect(self._show_error_message)
        self._segment_manager.segments_updated.connect(self._controlled_player.set_segment_markers)
        self._segment_manager.start_marker_updated.connect(self._controlled_player.set_current_start_marker)

        self._segment_manager.segment_added.connect(self._segment_list.add_segment)
        self._segment_manager.segment_updated.connect(self._segment_list.update_segment)
        self._segment_manager.segment_removed.connect(self._segment_list.takeItem)
        self._segment_manager.selection_cleared.connect(self._segment_list.clearSelection)

        self._processor.processing_started.connect(self._on_processing_started)
        self._processor.processing_stopped.connect(self._on_processing_stopped)
        self._processor.status_updated.connect(self._on_processor_status_update)
        self._processor.segment_processed.connect(self._on_segment_processed)
        self._processor.log_signal.connect(self._logger.append_log)

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
        self._controlled_player.update_duration(duration)
        self._controlled_player.update_position(self._controlled_player.position(), duration)
        
    def _on_position_changed(self, position):
        """Slot to handle the player's positionChanged signal."""
        self._controlled_player.update_position(position, self._controlled_player.duration())

    # ==================================================================
    # Segment Manager Slots
    # ==================================================================
    def _on_set_start_time(self):
        """Handles the event when the start time button is clicked."""
        self._segment_manager.set_start_time(self._controlled_player.position())
        self._controlled_player.pause()
    
    def _on_set_end_time(self):
        """Handles the event when the end time button is clicked."""
        self._segment_manager.set_end_time(self._controlled_player.position())
        self._controlled_player.pause()

    # ==================================================================
    # Processor Slots
    # ==================================================================
    def _update_ui_state(self, state: str):
        """Enables or disables UI controls based on processing state."""
        if state == "enable":
            self._action_panel.update_ui_state('enable')
            self._controlled_player.setEnabled(True)
            self._segment_list.setEnabled(True)
            self._placeholders_table.setEnabled(True)
            self._cmd_template.setEnabled(True)
        elif state == "disable":
            self._action_panel.update_ui_state('disable')
            self._controlled_player.setDisabled(True)
            self._segment_list.setDisabled(True)
            self._placeholders_table.setDisabled(True)
            self._cmd_template.setDisabled(True)
        else:
            return

    def _on_processing_started(self, total_segments: int):
        """Handles the start of the segment processing task."""
        self._update_ui_state('disable')
        self._controlled_player.pause()
        for i in range(total_segments):
            self._segment_list.highlight_row(i, self._PENDING_COLOR)
        self._logger.append_log(styled_text('bold', 'blue', None, f'Features: Video Cutter | '
                                                                    f'Start processing {total_segments} segments...'))

    def _on_processing_stopped(self):
        """Handles the end of the segment processing task."""
        self._update_ui_state('enable')
        self._segment_list.clear_highlights()
        self._logger.append_log(styled_text('bold', 'blue', None, "Features: Video Cutter | "
                                                                    f"Stopped cutting processes..."))

    def _on_segment_processed(self, segment_data: tuple[int, int]):
        self._segment_manager.delete_segment_by_data(segment_data)
        log_message = styled_text('bold', 'green', None, 
                                  f'Features: Video Cutter | '
                                  f'Processed: Segment ({ms_to_time_str(segment_data[0])}, {ms_to_time_str(segment_data[1])})')
        self._logger.append_log(log_message)

    def _on_processor_status_update(self, segment_data: tuple[int, int], status: str):
        """Highlights the segment row based on its processing status."""
        row = self._segment_list.find_segment_by_data(segment_data)
        if row != -1:
            if status == "Processing":
                self._segment_list.highlight_row(row, self._PROCESSING_COLOR)
            elif status == "Stopped":
                self._segment_list.clear_highlight(row)
        else:
            self._logger.append_log(styled_text('bold', 'red', None, 
                                                f'Features: Video Cutter | '
                                                f'Could not find segment ({ms_to_time_str(segment_data[0])}, {ms_to_time_str(segment_data[1])}) '
                                                f'in the list to update status.'))

    def _on_cut_clicked(self):
        self._controlled_player.pause()
        segments = self._segment_manager.get_segments_for_processing()
        if not segments:
            return
        jobs = []
        for segment in segments:
            start_ms, end_ms = segment
            commands = self._cmd_template.generate_commands(input_file=self._input_file,
                                                            output_folder=self._output_folder,
                                                            start_ms=start_ms,
                                                            end_ms=end_ms)
            if not commands:
                self._show_error_message("Command Error", "Could not generate command. Check the command template.")
                return # Stop if any command fails to generate
            
            jobs.append((str(segment), commands))
        self._processor.start(jobs)

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
        selected_segment = self._segment_manager.get_segment_by_index(segment_index)
        if selected_segment:
            self._controlled_player.set_position(selected_segment[0])
            self._controlled_player.pause()

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
            self._segment_manager.delete_segment_by_index(row)

    def _edit_segment(self, row: int):
        """Handles the logic for editing a segment via a dialog."""
        segment = self._segment_manager.get_segment_by_index(row)
        if not segment:
            return

        start_ms, end_ms = segment
        dialog = EditSegmentDialog(self, start_ms, end_ms)

        if dialog.exec_() == QDialog.Accepted:
            new_start, new_end = dialog.get_edited_times()
            if self._segment_manager.update_segment(row, new_start, new_end):
                self._segment_list.setCurrentRow(row)
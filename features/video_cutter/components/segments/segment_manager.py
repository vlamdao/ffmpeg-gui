from PyQt5.QtCore import QObject, pyqtSignal, QTime
from PyQt5.QtWidgets import QDialog

from .edit_segment_dialog import EditSegmentDialog
from helper import ms_to_time_str

class SegmentManager(QObject):
    """Manages the state and logic for creating, editing, and deleting video segments."""

    # Signals to notify the main widget about UI updates
    segments_updated = pyqtSignal(list)
    current_start_marker_updated = pyqtSignal(int)
    labels_updated = pyqtSignal(dict)
    list_item_added = pyqtSignal(str)
    list_item_updated = pyqtSignal(int, str)
    list_item_removed = pyqtSignal(int)
    list_selection_cleared = pyqtSignal()
    list_cleared = pyqtSignal()
    error_occurred = pyqtSignal(str, str) # title, message

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.segments: list[tuple[int, int]] = []
        self.start_time: int | None = None
        self.selected_index: int = -1

    def set_start_time(self, time_ms: int) -> None:
        """Sets the start time for a new segment or updates an existing one."""
        if self.selected_index != -1:
            self._update_selected_segment(start_ms=time_ms)
        else:
            self.start_time = time_ms
            self.current_start_marker_updated.emit(self.start_time)
            self.labels_updated.emit({'start': self.start_time})

    def set_end_time(self, time_ms: int) -> None:
        """Updates the end time of the currently selected segment."""
        if self.selected_index != -1:
            self._update_selected_segment(end_ms=time_ms)
            self.list_selection_cleared.emit() # Deselect after editing is complete
        else:
            # This case is handled by create_segment now
            self.error_occurred.emit("Invalid Action", "Please select a segment to edit its end time, or set a start time to create a new segment.")

    def create_segment(self, end_time_ms: int) -> None:
        """Creates and adds a new segment using the stored start time."""
        if self.start_time is None:
            self.error_occurred.emit("Incomplete Segment", "Please set a start time first.")
            return
        if self.start_time >= end_time_ms:
            self.error_occurred.emit("Invalid Segment", "End time must be after start time.")
            return

        segment = (self.start_time, end_time_ms)
        self.segments.append(segment)

        self.list_item_added.emit(self._get_item_text(self.start_time, end_time_ms))
        self.segments_updated.emit(self.segments)

        # Reset for the next new segment
        self.start_time = None
        self.current_start_marker_updated.emit(-1)
        self.labels_updated.emit({'reset': True})

    def _update_selected_segment(self, start_ms: int | None = None, end_ms: int | None = None) -> None:
        """Internal helper to update the currently selected segment."""
        if not (0 <= self.selected_index < len(self.segments)):
            return

        current_start, current_end = self.segments[self.selected_index]
        new_start = start_ms if start_ms is not None else current_start
        new_end = end_ms if end_ms is not None else current_end

        if new_start >= new_end:
            self.error_occurred.emit("Invalid Time", "Start time must be before the end time.")
            return

        self.segments[self.selected_index] = (new_start, new_end)
        self.list_item_updated.emit(self.selected_index, self._get_item_text(new_start, new_end))
        self.segments_updated.emit(self.segments)
        self.labels_updated.emit({'start': new_start, 'end': new_end})

    def handle_selection_change(self, selected_row: int) -> tuple[int, int]:
        """Handles logic when a segment is selected or deselected in the list."""
        if selected_row == -1:
            # Deselection
            self.selected_index = -1
            if self.start_time is None: # Don't reset if user is defining a new segment
                self.labels_updated.emit({'reset': True})
            self.current_start_marker_updated.emit(-1)
            return -1, -1 # No position change

        # Selection
        self.selected_index = selected_row
        if not (0 <= self.selected_index < len(self.segments)):
            self.clear_all()
            return -1, -1

        start_ms, end_ms = self.segments[self.selected_index]
        self.start_time = None # Clear any pending new segment
        self.current_start_marker_updated.emit(-1)
        self.labels_updated.emit({'start': start_ms, 'end': end_ms})
        return start_ms, end_ms # Return position to seek to

    def edit_segment(self, row: int) -> int:
        """Opens a dialog to edit a segment and updates it if accepted."""
        if not (0 <= row < len(self.segments)):
            return -1

        start_ms, end_ms = self.segments[row]
        dialog = EditSegmentDialog(self.parent(), start_ms, end_ms)

        if dialog.exec_() == QDialog.Accepted:
            new_start, new_end = dialog.get_edited_times()
            self.segments[row] = (new_start, new_end)
            self.list_item_updated.emit(row, self._get_item_text(new_start, new_end))
            self.segments_updated.emit(self.segments)
            return row # Return row to select
        return -1

    def delete_segment(self, row: int) -> None:
        if not (0 <= row < len(self.segments)):
            return

        self.segments.pop(row)
        self.list_item_removed.emit(row)
        self.segments_updated.emit(self.segments)

        if self.selected_index == row:
            self.list_selection_cleared.emit()
        elif self.selected_index > row:
            self.selected_index -= 1

    def clear_all(self) -> None:
        self.segments.clear()
        self.start_time = None
        self.selected_index = -1
        self.list_cleared.emit()
        self.segments_updated.emit([])
        self.current_start_marker_updated.emit(-1)
        self.labels_updated.emit({'reset': True})

    def update_dynamic_end_label(self, position: int) -> None:
        """Updates the 'End' label dynamically as the player position changes."""
        if self.start_time is not None and self.selected_index == -1:
            self.labels_updated.emit({'end': position})

    def get_segments_for_processing(self) -> list[tuple[int, int]] | None:
        if not self.segments:
            self.error_occurred.emit("No Segments", "Please add at least one segment to cut.")
            return None
        return self.segments

    def _get_item_text(self, start_ms: int, end_ms: int) -> str:
        return f"{ms_to_time_str(start_ms)} -> {ms_to_time_str(end_ms)}"

    def get_all_item_texts(self) -> list[str]:
        return [self._get_item_text(s, e) for s, e in self.segments]
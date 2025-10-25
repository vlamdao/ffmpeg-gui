from PyQt5.QtCore import QObject, pyqtSignal, QTime
from PyQt5.QtWidgets import QDialog

from .edit_segment_dialog import EditSegmentDialog
from helper import ms_to_time_str

class SegmentManager(QObject):
    """Manages the state and logic for creating, editing, and deleting video segments.

    This class acts as the central "brain" for segment-related operations.
    It maintains the list of segments and the state of the current operation (e.g.,
    creating a new segment, selecting an existing one). It is completely decoupled
    from the user interface and communicates its state changes via Qt signals.
    """

    # --- Public Signals ---

    segments_updated = pyqtSignal(list)
    """Emitted whenever the segment list changes (add, update, delete, clear)."""

    current_start_marker_updated = pyqtSignal(int)
    """Emitted to update the position of the pending 'start' marker on the slider."""

    display_times_updated = pyqtSignal(dict)
    """Emitted to update the 'Start' and 'End' time labels on the UI."""

    error_occurred = pyqtSignal(str, str) # title, message
    """Emitted when a logical error occurs (e.g., end time is before start time)."""
    
    # Signals for granular UI updates, allowing the view to update efficiently without
    # needing to redraw the entire list.
    segment_added = pyqtSignal(int, int)
    """Emitted when a new segment is added, containing (start_ms, end_ms)."""
    segment_updated = pyqtSignal(int, int, int)
    """Emitted when a segment is updated, containing (row, new_start_ms, new_end_ms)."""
    segment_removed = pyqtSignal(int)
    """Emitted when a segment is deleted, containing the row index that was removed."""
    list_cleared = pyqtSignal()
    """Emitted when all segments have been cleared."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.segments: list[tuple[int, int]] = []
        self.start_time: int | None = None
        self.selected_index: int = -1

    def set_start_time(self, time_ms: int) -> None:
        """Sets the start time for a new segment or updates an existing one.

        This method has a dual purpose:
        1. If a segment is currently selected, it updates that segment's start time.
        2. Otherwise, it begins the creation of a new segment by storing the start time.
        """
        if self.selected_index != -1:
            # Update the start time of the currently selected segment.
            self._update_selected_segment(start_ms=time_ms)
        else:
            # Begin a new segment.
            self.start_time = time_ms
            self.current_start_marker_updated.emit(self.start_time)
            self.display_times_updated.emit({'start': self.start_time})

    def create_segment(self, end_time_ms: int) -> None:
        """Finalizes and adds a new segment using the stored start time.
        """
        if self.start_time is None:
            self.error_occurred.emit("Incomplete Segment", "Please set a start time first.")
            return
        if self.start_time >= end_time_ms:
            self.error_occurred.emit("Invalid Segment", "End time must be after start time.")
            return

        segment = (self.start_time, end_time_ms)
        self.segments.append(segment)
        self.segment_added.emit(self.start_time, end_time_ms)
        self.segments_updated.emit(self.segments)

        # Reset state to prepare for the next new segment.
        self.start_time = None
        self.current_start_marker_updated.emit(-1)
        self.display_times_updated.emit({'reset': True})

    def _update_selected_segment(self, start_ms: int | None = None, end_ms: int | None = None) -> None:
        """Internal helper to update the data of the currently selected segment."""
        if not (0 <= self.selected_index < len(self.segments)):
            return

        current_start, current_end = self.segments[self.selected_index]
        new_start = start_ms if start_ms is not None else current_start
        new_end = end_ms if end_ms is not None else current_end

        if new_start >= new_end:
            self.error_occurred.emit("Invalid Time", "Start time must be before the end time.")
            return
        
        new_segment = (new_start, new_end)
        self.segments[self.selected_index] = new_segment
        self.segment_updated.emit(self.selected_index, new_start, new_end)
        self.segments_updated.emit(self.segments)
        self.display_times_updated.emit({'start': new_start, 'end': new_end})

    def handle_selection_change(self, selected_row: int) -> tuple[int, int]:
        """Handles logic when a segment is selected or deselected in the list.

        Returns:
            A tuple (start_ms, end_ms) of the selected segment to seek to,
            or (-1, -1) if no action is needed.
        """
        if selected_row == -1:
            # If a new segment is being defined (start time is set), do nothing on deselection
            # to avoid interrupting the user's workflow.
            if self.start_time is not None:
                return -1, -1
            # Deselection: Reset selection state and UI.
            self.selected_index = -1
            self.display_times_updated.emit({'reset': True})
            self.current_start_marker_updated.emit(-1)
            return -1, -1 # No position change

        # An item was selected:
        self.selected_index = selected_row
        if not (0 <= self.selected_index < len(self.segments)):
            self.clear_all()
            return -1, -1

        start_ms, end_ms = self.segments[self.selected_index]
        self.start_time = None # Clear any pending new segment
        # Clear any "new segment" state because the user has selected an existing item.
        self.current_start_marker_updated.emit(-1)
        self.display_times_updated.emit({'start': start_ms, 'end': end_ms})
        return start_ms, end_ms # Return position to seek to.

    def edit_segment(self, row: int) -> int:
        """Opens a dialog to edit a segment and updates it if accepted.
        """
        if not (0 <= row < len(self.segments)):
            return -1

        start_ms, end_ms = self.segments[row]
        dialog = EditSegmentDialog(self.parent(), start_ms, end_ms)

        if dialog.exec_() == QDialog.Accepted:
            new_start, new_end = dialog.get_edited_times()
            # Temporarily set selected_index to reuse the update logic
            # in _update_selected_segment.
            self.selected_index = row
            self._update_selected_segment(start_ms=new_start, end_ms=new_end)
            return row # Return the row so the UI can re-select it.
        return -1

    def delete_segment(self, row: int) -> None:
        """Deletes a segment from the list at a given row."""
        if not (0 <= row < len(self.segments)):
            return

        self.segments.pop(row)
        self.segment_removed.emit(row)
        self.segments_updated.emit(self.segments)

        # Update internal selection index after deletion.
        if self.selected_index == row:
            # The deleted item was the selected one.
            self.selected_index = -1
        elif self.selected_index > row:
            # The deleted item was before the selected one, so shift the index down.
            self.selected_index -= 1

    def clear_all(self) -> None:
        """Clears all segments and resets the state to its initial values."""
        self.segments.clear()
        self.start_time = None
        self.selected_index = -1
        self.list_cleared.emit()
        self.segments_updated.emit([])
        self.current_start_marker_updated.emit(-1)
        self.display_times_updated.emit({'reset': True})

    def update_preview_end_time(self, position: int) -> None:
        """Emits a signal to update the 'End' time display for a live preview while
        creating a new segment.
        """
        if self.start_time is not None and self.selected_index == -1:
            self.display_times_updated.emit({'end': position})

    def get_segments_for_processing(self) -> list[tuple[int, int]] | None:
        """Gets the list of segments for processing (e.g., for cutting the video)."""
        if not self.segments:
            self.error_occurred.emit("No Segments", "Please add at least one segment to cut.")
            return None
        return self.segments
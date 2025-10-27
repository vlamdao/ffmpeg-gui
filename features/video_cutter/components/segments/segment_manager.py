from enum import Enum, auto
from PyQt5.QtCore import QObject, pyqtSignal, QTime
from PyQt5.QtWidgets import QDialog

from .edit_segment_dialog import EditSegmentDialog
from helper import ms_to_time_str

class SegmentState(Enum):
    """Defines the possible states for the segment management logic."""
    IDLE = auto()  # Ready to create a new segment.
    CREATING = auto()  # A start time has been set, waiting for an end time.
    EDITING = auto()  # An existing segment is selected for modification.

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
    selection_cleared = pyqtSignal()
    """Emitted to explicitly clear selection in the view."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.segments: list[tuple[int, int | None]] = []
        self._state: SegmentState = SegmentState.IDLE
        print(f"State changed to: {self._state}")
        self._active_segment_index: int = -1

    def set_start_time(self, time_ms: int) -> None:
        """Sets the start time for a new segment or updates an existing one.

        This method has a dual purpose:
        1. If a segment is currently selected, it updates that segment's start time.
        2. Otherwise, it begins the creation of a new segment by storing the start time.
        """
        if self._state == SegmentState.EDITING:
            self._update_selected_segment(start_ms=time_ms)
        elif self._state == SegmentState.IDLE:
            # Create a new segment with a start time and a placeholder for the end time.
            new_segment = (time_ms, None)
            self.segments.append(new_segment)
            self._active_segment_index = len(self.segments) - 1
            self._state = SegmentState.CREATING
            print(f"State changed to: {self._state}")

            self.segment_added.emit(time_ms, -1) # Use -1 to indicate incomplete end time
            self.current_start_marker_updated.emit(time_ms)

    def create_segment(self, end_time_ms: int) -> None:
        """Finalizes a new segment or updates the end time of a selected one.
        """
        update_successful = False
        if self._state == SegmentState.CREATING:
            update_successful = self._update_selected_segment(end_ms=end_time_ms)
            if update_successful:
                self._state = SegmentState.IDLE
                print(f"State changed to: {self._state}")
                self._reset_to_idle_state() # Resets index and clears selection
        elif self._state == SegmentState.EDITING:
            self._update_selected_segment(end_ms=end_time_ms)

    def _reset_to_idle_state(self):
        """Resets the manager to the initial IDLE state."""
        self._active_segment_index = -1
        self.current_start_marker_updated.emit(-1)
        self.selection_cleared.emit()

    def _update_selected_segment(self, start_ms: int | None = None, end_ms: int | None = None) -> bool:
        """Internal helper to update the data of the currently selected segment."""
        if not (0 <= self._active_segment_index < len(self.segments)):
            return False

        current_start, current_end = self.segments[self._active_segment_index]
        new_start = start_ms if start_ms is not None else current_start
        new_end = end_ms if end_ms is not None else current_end

        # Allow end_ms to be None during creation
        if new_end is not None and new_start >= new_end:
            self.error_occurred.emit("Invalid Time", "Start time must be before the end time.")
            # If this error happened during creation, it's better to cancel the
            # operation automatically so the user doesn't have a dangling "[creating...]" item.
            if self._state == SegmentState.CREATING:
                self.cancel_creation()
            return False
        
        new_segment = (new_start, new_end)
        self.segments[self._active_segment_index] = new_segment
        self.segment_updated.emit(self._active_segment_index, new_start, new_end if new_end is not None else -1)
        self.segments_updated.emit(self.segments)
        return True

    def handle_selection_change(self, selected_row: int) -> tuple[int, int]:
        """Handles logic when a segment is selected or deselected in the list.

        Returns:
            A tuple (start_ms, end_ms) of the selected segment to seek to,
            or (-1, -1) if no action is needed.
        """
        # If a new segment is currently being created, do not process selection changes.
        # This prevents the selection of the newly added "[creating...]" item from
        # immediately switching the state to EDITING.
        if self._state == SegmentState.CREATING:
            return -1, -1

        if selected_row == -1: # Deselection
            self._state = SegmentState.IDLE
            print(f"State changed to: {self._state}")
            self._reset_to_idle_state() # Resets index and clears selection
            return -1, -1 # No position change

        # An item was selected:
        self._active_segment_index = selected_row
        if not (0 <= self._active_segment_index < len(self.segments)):
            self.clear_all()
            return -1, -1

        start_ms, end_ms = self.segments[self._active_segment_index]

        # If the selected segment is incomplete, it's an error state. Reset.
        if end_ms is None:
            self.clear_all()
            return -1, -1

        self._state = SegmentState.EDITING
        print(f"State changed to: {self._state}")
        self.current_start_marker_updated.emit(-1)
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
            self._active_segment_index = row
            self._state = SegmentState.EDITING
            print(f"State changed to: {self._state}")
            if self._update_selected_segment(start_ms=new_start, end_ms=new_end):
                return row # Return the row so the UI can re-select it.
        return -1

    def cancel_creation(self) -> bool:
        """Cancels the creation of a new segment if in the CREATING state.

        Returns:
            bool: True if a creation was cancelled, False otherwise.
        """
        if self._state == SegmentState.CREATING and self._active_segment_index != -1:
            self.delete_segment(self._active_segment_index)
            return True
        return False

    def delete_segment(self, row: int) -> None:
        """Deletes a segment from the list at a given row."""
        if not (0 <= row < len(self.segments)):
            return

        self.segments.pop(row)
        self.segment_removed.emit(row)
        self.segments_updated.emit(self.segments)

        # After any deletion, always reset to the clean IDLE state
        # which also clears the selection in the view.
        self._state = SegmentState.IDLE
        print(f"State changed to: {self._state}")
        self._reset_to_idle_state()

    def clear_all(self) -> None:
        """Clears all segments and resets the state to its initial values."""
        self.segments.clear()
        self.list_cleared.emit()
        self.segments_updated.emit([])
        self._state = SegmentState.IDLE
        print(f"State changed to: {self._state}")
        self._reset_to_idle_state()

    def get_segments_for_processing(self) -> list[tuple[int, int]] | None:
        """Gets the list of segments for processing (e.g., for cutting the video)."""
        # Filter out any incomplete segments before processing
        complete_segments = [seg for seg in self.segments if seg[1] is not None]

        if not complete_segments:
            self.error_occurred.emit("No Segments", "Please add at least one segment to cut.")
            return None
        return complete_segments
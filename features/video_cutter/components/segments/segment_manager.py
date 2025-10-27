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

    start_marker_updated = pyqtSignal(int)
    """Emitted to update the position of the pending 'start' marker on the slider."""

    error_occurred = pyqtSignal(str, str) # title, message
    """Emitted when a logical error occurs (e.g., end time is before start time)."""

    segment_added = pyqtSignal(int, int)
    """Emitted when a new segment is added, containing (start_ms, end_ms)."""
    
    segment_updated = pyqtSignal(int, int, int)
    """Emitted when a segment is updated, containing (row, new_start_ms, new_end_ms)."""
    
    segment_removed = pyqtSignal(int)
    """Emitted when a segment is deleted, containing the row index that was removed."""
    
    selection_cleared = pyqtSignal()
    """Emitted to explicitly clear selection in the view."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.segments: list[tuple[int, int | None]] = []
        self._state: SegmentState = SegmentState.IDLE # Initial state
        self._set_state(SegmentState.IDLE) # Set initial state via the new method
        self._current_segment_index: int = -1

    def _set_state(self, new_state: SegmentState):
        """Centralized method for changing the state and logging it."""
        if self._state != new_state:
            self._state = new_state
            print(f"State changed to: {self._state}")
    
    def _reset_to_idle_state(self):
        """Resets the manager to the initial IDLE state."""
        self._current_segment_index = -1
        self.start_marker_updated.emit(-1)
        self.selection_cleared.emit()
    
    def _is_selected_segment_valid(self, segment_index: int) -> bool:
        """Checks if the currently selected segment index is valid."""
        return 0 <= segment_index < len(self.segments)

    def _update_selected_segment(self, start_ms: int | None = None, end_ms: int | None = None) -> bool:
        """Internal helper to update the data of the currently selected segment."""
        if not self._is_selected_segment_valid(self._current_segment_index):
            return False

        current_start, current_end = self.segments[self._current_segment_index]
        new_start = start_ms if start_ms is not None else current_start
        new_end = end_ms if end_ms is not None else current_end

        # If the new end time is before or equal to the start time
        # Emit an error and cancel the operation.
        if new_end is not None and new_end <= new_start:
            self.error_occurred.emit("Invalid Time", "Start time must be before the end time.")
            if self._state == SegmentState.CREATING:
                self.cancel_creation()
            return False
        
        new_segment = (new_start, new_end)
        self.segments[self._current_segment_index] = new_segment
        if new_end is not None:
            self.segment_updated.emit(self._current_segment_index, new_start, new_end)
        else:
            self.segment_updated.emit(self._current_segment_index, new_start, -1)
        self.segments_updated.emit(self.segments)

        # If we just finished creating a segment, transition back to IDLE.
        if self._state == SegmentState.CREATING and new_end is not None:
            self._set_state(SegmentState.IDLE)
            self._reset_to_idle_state()
        return True

    def set_start_time(self, time_ms: int) -> None:
        """Sets the start time for a new segment or updates an existing one.

        This method has a dual purpose:
        - In `EDITING` state: Updates the start time of the currently selected segment.
        - In `IDLE` state: Begins the creation of a new segment, transitioning the
          state to `CREATING`.
        """
        if self._state == SegmentState.EDITING:
            self._update_selected_segment(start_ms=time_ms)
        elif self._state == SegmentState.IDLE:
            # Create a new segment with a start time and a placeholder for the end time.
            new_segment = (time_ms, None)
            self.segments.append(new_segment)
            self._current_segment_index = len(self.segments) - 1
            self._set_state(SegmentState.CREATING)

            self.segment_added.emit(time_ms, -1) # Use -1 to indicate incomplete end time
            self.start_marker_updated.emit(time_ms)

    def set_end_time(self, end_time_ms: int) -> None:
        """Sets the end time, either finalizing a new segment or updating an existing one.

        - In `CREATING` state: Finalizes the new segment and returns to `IDLE`.
        - In `EDITING` state: Updates the end time of tcurrently selected segment.
        """
        if self._state == SegmentState.CREATING or self._state == SegmentState.EDITING:
            self._update_selected_segment(end_ms=end_time_ms)

    def handle_segment_selection(self, segment_index: int) -> None:
        """Prepares the manager for editing a segment based on a row selection.

        This function transitions the state machine. If the selection is valid,
        it enters the EDITING state. If the selection is invalid (or deselected),
        it reverts to the IDLE state.
        """

        if self._state == SegmentState.CREATING:
            return
        
        if not self._is_selected_segment_valid(segment_index):
            self._set_state(SegmentState.IDLE)
            self._reset_to_idle_state()
            return

        # If the selection is valid, update the state to EDITING.
        self._current_segment_index = segment_index
        self._set_state(SegmentState.EDITING)
        self.start_marker_updated.emit(-1)

    def get_segment_at(self, segment_index: int) -> tuple[int, int] | None:
        """
        Retrieves the segment data at a specific segment_index.

        This is a pure "query" method that does not change any state.

        Returns:
            A tuple (start_ms, end_ms) if the segment_index is valid and the segment is
            complete, otherwise None.
        """
        if not self._is_selected_segment_valid(segment_index):
            return None
        start_ms, end_ms = self.segments[segment_index]
        return (start_ms, end_ms) if end_ms is not None else None

    def edit_segment_with_dialog(self, segment_index: int) -> int:
        """Opens a dialog to edit a segment and updates it if accepted.
        """
        if not self._is_selected_segment_valid(segment_index):
            return -1

        start_ms, end_ms = self.segments[segment_index]
        dialog = EditSegmentDialog(self.parent(), start_ms, end_ms)

        if dialog.exec_() == QDialog.Accepted:
            new_start, new_end = dialog.get_edited_times()
            self._current_segment_index = segment_index
            self._set_state(SegmentState.EDITING)
            if self._update_selected_segment(start_ms=new_start, end_ms=new_end):
                return segment_index # Return the segment_index so the UI can re-select it.
        return -1

    def cancel_creation(self) -> bool:
        """Cancels the creation of a new segment if in the CREATING state.

        Returns:
            bool: True if a creation was cancelled, False otherwise.
        """
        if self._state == SegmentState.CREATING and self._current_segment_index != -1:
            self.delete_segment(self._current_segment_index)
            return True
        return False

    def delete_segment(self, segment_index: int) -> None:
        """Deletes a segment from the list at a given segment_index."""
        if not self._is_selected_segment_valid(segment_index):
            return

        self.segments.pop(segment_index)
        self.segment_removed.emit(segment_index)
        self.segments_updated.emit(self.segments)

        # After any deletion, always reset to the clean IDLE state
        # which also clears the selection in the view.
        self._set_state(SegmentState.IDLE)
        self._reset_to_idle_state()

    def get_segments_for_processing(self) -> list[tuple[int, int]] | None:
        """Gets the list of segments for processing (e.g., for cutting the video)."""
        # Filter out any incomplete segments before processing
        complete_segments = [seg for seg in self.segments if seg[1] is not None]

        if not complete_segments:
            self.error_occurred.emit("No Segments", "Please add at least one segment to cut.")
            return None
        return complete_segments
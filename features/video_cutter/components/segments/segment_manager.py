from PyQt5.QtCore import QObject, pyqtSignal, QTime
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QDialog

from .edit_segment_dialog import EditSegmentDialog

class SegmentManager(QObject):
    """Manages the state and logic for video segments."""

    # Signals to notify the main widget about UI updates
    segments_updated = pyqtSignal(list)
    current_start_marker_updated = pyqtSignal(int)
    labels_updated = pyqtSignal(dict)
    list_item_added = pyqtSignal(str)
    list_item_updated = pyqtSignal(int, str)
    list_item_removed = pyqtSignal(int)
    list_selection_cleared = pyqtSignal()
    list_cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self.start_time = None
        self.selected_index = -1

    def _ms_to_time_str(self, ms):
        time = QTime(0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")

    def set_start_time(self, current_pos):
        if self.selected_index != -1:  # Editing an existing segment
            _, end_time = self.segments[self.selected_index]
            if current_pos >= end_time:
                QMessageBox.warning(self.parent(), "Invalid Time", "Start time must be before the segment's end time.")
                return
            self.segments[self.selected_index] = (current_pos, end_time)
            self.list_item_updated.emit(self.selected_index, self._get_item_text(current_pos, end_time))
            self.segments_updated.emit(self.segments)
            self.labels_updated.emit({'start': current_pos})
        else:  # Setting start for a new segment
            self.start_time = current_pos
            self.current_start_marker_updated.emit(self.start_time)
            self.labels_updated.emit({'start': self.start_time})

    def set_end_time(self, current_pos):
        if self.selected_index != -1:  # Editing an existing segment's end time
            start_time, _ = self.segments[self.selected_index]
            if current_pos <= start_time:
                QMessageBox.warning(self.parent(), "Invalid Time", "End time must be after the segment's start time.")
                return
            self.segments[self.selected_index] = (start_time, current_pos)
            self.list_item_updated.emit(self.selected_index, self._get_item_text(start_time, current_pos))
            self.segments_updated.emit(self.segments)
            self.labels_updated.emit({'end': current_pos})
            self.list_selection_cleared.emit() # Deselect after editing
            return

        # Adding a new segment
        if self.start_time is None:
            QMessageBox.warning(self.parent(), "Incomplete Segment", "Please set a start time first.")
            return
        if self.start_time >= current_pos:
            QMessageBox.warning(self.parent(), "Invalid Segment", "End time must be after start time.")
            return

        segment = (self.start_time, current_pos)
        self.segments.append(segment)

        self.list_item_added.emit(self._get_item_text(self.start_time, current_pos))
        self.segments_updated.emit(self.segments)
        self.current_start_marker_updated.emit(-1)
        self.start_time = None
        self.labels_updated.emit({'reset': True})

    def handle_selection_change(self, selected_row):
        if selected_row == -1:
            self.selected_index = -1
            self.start_time = None
            self.current_start_marker_updated.emit(-1)
            self.labels_updated.emit({'reset': True})
            return -1, -1 # No position change

        self.selected_index = selected_row
        if not (0 <= self.selected_index < len(self.segments)):
            self.clear_all()
            return -1, -1

        start_ms, end_ms = self.segments[self.selected_index]
        self.labels_updated.emit({'start': start_ms, 'end': end_ms})
        return start_ms, end_ms # Return position to seek to

    def edit_segment(self, row):
        if not (0 <= row < len(self.segments)): return

        start_ms, end_ms = self.segments[row]
        dialog = EditSegmentDialog(self.parent(), start_ms, end_ms)
        if dialog.exec_() == QDialog.Accepted:
            new_start, new_end = dialog.get_edited_times()
            self.segments[row] = (new_start, new_end)
            self.list_item_updated.emit(row, self._get_item_text(new_start, new_end))
            self.segments_updated.emit(self.segments)
            return row # Return row to select
        return -1

    def delete_segment(self, row):
        if not (0 <= row < len(self.segments)): return

        self.segments.pop(row)
        self.list_item_removed.emit(row)
        self.segments_updated.emit(self.segments)

        if self.selected_index == row:
            self.list_selection_cleared.emit()
        elif self.selected_index > row:
            self.selected_index -= 1

    def clear_all(self):
        self.segments.clear()
        self.start_time = None
        self.selected_index = -1
        self.list_cleared.emit()
        self.segments_updated.emit([])
        self.current_start_marker_updated.emit(-1)
        self.labels_updated.emit({'reset': True})

    def update_dynamic_end_label(self, position):
        if self.start_time is not None and self.selected_index == -1:
            self.labels_updated.emit({'end': position})

    def get_segments_for_processing(self):
        if not self.segments:
            QMessageBox.warning(self.parent(), "No Segments", "Please add at least one segment to cut.")
            return None
        return self.segments

    def _get_item_text(self, start_ms, end_ms):
        return f"{self._ms_to_time_str(start_ms)} -> {self._ms_to_time_str(end_ms)}"

    def get_all_item_texts(self):
        return [self._get_item_text(s, e) for s, e in self.segments]
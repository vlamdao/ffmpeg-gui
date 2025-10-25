from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from helper import ms_to_time_str

class DeselectableListWidget(QListWidget):
    """A QListWidget that allows deselecting items by clicking outside."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if not self.itemAt(event.pos()):
            self.clearSelection()
        super().mousePressEvent(event)
        
class SegmentList(DeselectableListWidget):
    """A view widget for displaying the list of video segments.

    This class acts as a passive view component. It receives commands from a
    controller (via signals/slots) to add, update, or remove items from the
    list. It does not contain any business logic itself.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(275)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def _create_item(self, start_ms: int, end_ms: int) -> QListWidgetItem:
        """Creates a QListWidgetItem with embedded segment data."""
        text = f"{ms_to_time_str(start_ms)} -> {ms_to_time_str(end_ms)}"
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, (start_ms, end_ms))
        return item

    def add_segment(self, start_ms: int, end_ms: int):
        """Adds a new segment to the list."""
        item = self._create_item(start_ms, end_ms)
        self.addItem(item)

    def update_segment(self, row: int, start_ms: int, end_ms: int):
        """Updates an existing segment in the list."""
        item = self.item(row)
        if item:
            item.setText(f"{ms_to_time_str(start_ms)} -> {ms_to_time_str(end_ms)}")
            item.setData(Qt.UserRole, (start_ms, end_ms))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget

class DeselectableListWidget(QListWidget):
    """A QListWidget that allows deselecting items by clicking outside."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if not self.itemAt(event.pos()):
            self.clearSelection()
        super().mousePressEvent(event)
        
class SegmentList(DeselectableListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(275)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
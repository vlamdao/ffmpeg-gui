from PyQt5.QtCore import Qt
from .deselectable_list_widget import DeselectableListWidget

class SegmentList(DeselectableListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(275)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
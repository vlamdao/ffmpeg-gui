from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import pyqtSignal, Qt

class ClickableVideoWidget(QVideoWidget):
    """A QVideoWidget that emits a doubleClicked signal."""
    doubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
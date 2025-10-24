from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import pyqtSignal, Qt

class ClickableVideoWidget(QVideoWidget):
    """A QVideoWidget that emits a signal on double-click."""
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        """Override to emit a signal on double-click."""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
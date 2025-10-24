from PyQt5.QtWidgets import QListWidget

class DeselectableListWidget(QListWidget):
    """A QListWidget that clears selection when clicking on an empty area."""
    def mousePressEvent(self, event):
        # If we click on an empty area, clear the selection.
        # This will trigger the itemSelectionChanged signal.
        if not self.itemAt(event.pos()):
            self.clearSelection()
        # Call the base class implementation to handle normal item clicks.
        super().mousePressEvent(event)
from PyQt5.QtWidgets import (QDialog, QFormLayout, QTimeEdit, 
                             QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import QTime

class EditSegmentDialog(QDialog):
    """A dialog for editing the start and end times of a video segment."""
    def __init__(self, parent, initial_start_ms, initial_end_ms):
        super().__init__(parent)
        self.setWindowTitle("Edit Segment")
        self.setMinimumWidth(300)

        self.start_time_edit = QTimeEdit(self)
        self.end_time_edit = QTimeEdit(self)
        self.start_time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.end_time_edit.setDisplayFormat("HH:mm:ss.zzz")

        self.start_time_edit.setTime(QTime.fromMSecsSinceStartOfDay(initial_start_ms))
        self.end_time_edit.setTime(QTime.fromMSecsSinceStartOfDay(initial_end_ms))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Start Time:", self.start_time_edit)
        layout.addRow("End Time:", self.end_time_edit)
        layout.addWidget(buttons)

    def get_edited_times(self):
        """Returns the start and end times (in milliseconds) from the input fields."""
        start_ms = self.start_time_edit.time().msecsSinceStartOfDay()
        end_ms = self.end_time_edit.time().msecsSinceStartOfDay()
        return start_ms, end_ms

    def accept(self):
        """Override accept to add validation before closing the dialog."""
        start_ms, end_ms = self.get_edited_times()
        if start_ms >= end_ms:
            QMessageBox.warning(self, "Invalid Times", "Start time must be before end time.")
            return
        super().accept()
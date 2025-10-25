from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
                             QTimeEdit, QMessageBox)
from PyQt5.QtCore import QTime

class EditSegmentDialog(QDialog):
    def __init__(self, parent, start_ms, end_ms):
        super().__init__(parent)
        self.setWindowTitle("Edit Segment")
        self._initial_start_ms = start_ms
        self._initial_end_ms = end_ms

        self._start_time_edit: QTimeEdit
        self._end_time_edit: QTimeEdit

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Creates and arranges widgets in the dialog."""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self._start_time_edit = self._create_time_edit(self._initial_start_ms)
        self._end_time_edit = self._create_time_edit(self._initial_end_ms)

        form_layout.addRow("Start Time:", self._start_time_edit)
        form_layout.addRow("End Time:", self._end_time_edit)
        layout.addLayout(form_layout)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self._button_box)

    def _connect_signals(self):
        self._button_box.accepted.connect(self.validate_and_accept)
        self._button_box.rejected.connect(self.reject)

    def _create_time_edit(self, time_ms: int) -> QTimeEdit:
        """Factory method to create and configure a QTimeEdit widget."""
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm:ss.zzz")
        time_edit.setTime(QTime(0, 0, 0).addMSecs(time_ms))
        return time_edit

    def get_edited_times(self):
        """Returns the start and end times in milliseconds from the UI."""
        start_time = self._start_time_edit.time()
        end_time = self._end_time_edit.time()

        start_ms = QTime(0, 0, 0).msecsTo(start_time)
        end_ms = QTime(0, 0, 0).msecsTo(end_time)

        return start_ms, end_ms

    def validate_and_accept(self):
        start_ms, end_ms = self.get_edited_times()
        if start_ms >= end_ms:
            QMessageBox.warning(self, "Invalid Time", "End time must be after start time.")
            return

        self.accept()
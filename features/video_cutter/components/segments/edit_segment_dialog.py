from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
                             QTimeEdit)
from PyQt5.QtCore import QTime

class EditSegmentDialog(QDialog):
    def __init__(self, parent, start_ms, end_ms):
        super().__init__(parent)
        self.setWindowTitle("Edit Segment")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.start_time_edit.setTime(QTime(0, 0, 0).addMSecs(start_ms))

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.end_time_edit.setTime(QTime(0, 0, 0).addMSecs(end_ms))

        form_layout.addRow("Start Time:", self.start_time_edit)
        form_layout.addRow("End Time:", self.end_time_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_edited_times(self):
        start_time = self.start_time_edit.time()
        end_time = self.end_time_edit.time()

        start_ms = QTime(0, 0, 0).msecsTo(start_time)
        end_ms = QTime(0, 0, 0).msecsTo(end_time)

        return start_ms, end_ms
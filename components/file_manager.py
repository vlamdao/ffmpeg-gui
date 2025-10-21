from PyQt5.QtWidgets import (
    QTableWidgetItem, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QPixmap, QDesktopServices
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QUrl
import os
from utils import resource_path
from .delegate import FontDelegate
from processor import FileLoaderThread

class FileManager(QObject):
    log_signal = pyqtSignal(str)  # For logging messages

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.file_table = DragDropTable()
        self.file_loader_thread = None
        self.setup_file_table()

    def setup_file_table(self):
        """Setup the file table and its connections"""
        self.file_table.itemDoubleClicked.connect(self.open_file_on_doubleclick)
        self.file_table.files_dropped.connect(self.start_loading_files)

    def get_widget(self):
        """Return the file table widget"""
        return self.file_table

    def add_files_dialog(self):
        """Show dialog to add files"""
        files, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "Select files",
            "",
            "All files (*)"
        )
        if files:
            self.start_loading_files(files)

    def start_loading_files(self, file_list):
        """Start loading files in a separate thread"""
        if self.file_loader_thread is not None and self.file_loader_thread.isRunning():
            self.log_signal.emit("File loading already in progress. Please wait.")
            return
        self.file_loader_thread = FileLoaderThread(file_list)
        self.file_loader_thread.log_signal.connect(self.log_signal.emit)
        self.file_loader_thread.add_file_signal.connect(self.on_add_file_received)
        self.file_loader_thread.start()

    def on_add_file_received(self, filename, folder, duration_str, size_str):
        """Add a file to the table"""
        self.file_table.add_file(filename, folder, duration_str, size_str)

    def open_file_on_doubleclick(self, item):
        """Open file when double-clicked in table"""
        row = item.row()
        filename = self.file_table.item(row, 0).text()
        folder = self.file_table.item(row, 1).text()
        full_path = os.path.join(folder, filename)
        url = QUrl.fromLocalFile(full_path)
        if not QDesktopServices.openUrl(url):
            self.log_signal.emit(f"Cannot open file: {full_path}")

    def update_status(self, row, status):
        """Update the status of a file in the table"""
        icon_map = {
            "Processing": resource_path("icon/processing.png"),
            "Failed": resource_path("icon/failed.png"),
            "Successed": resource_path("icon/success.png"),
            "Pending": resource_path("icon/pending.png"),
            "Stopped": resource_path("icon/stop.png"),
        }
        if status in icon_map:
            label = QLabel()
            pixmap = QPixmap(icon_map[status])
            pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.status = status
            old_widget = self.file_table.cellWidget(row, 4)
            if old_widget:
                self.file_table.removeCellWidget(row, 4)
            self.file_table.setCellWidget(row, 4, label)
        elif status == "" or status is None:
            old_widget = self.file_table.cellWidget(row, 4)
            if old_widget:
                self.file_table.removeCellWidget(row, 4)
            self.file_table.setItem(row, 4, QTableWidgetItem(""))
        else:
            old_widget = self.file_table.cellWidget(row, 4)
            if old_widget:
                self.file_table.removeCellWidget(row, 4)
            item = QTableWidgetItem(status)
            item.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 4, item)

    def get_selected_files(self):
        """Get list of selected files from the table
    
        Returns:
            tuple: A tuple containing:
                - list: List of tuples (row, filename, folder) for each selected file
                - set: Set of selected row indices
            
        Example:
            files, selected_rows = file_manager.get_selected_files()
            # files = [(0, "video1.mp4", "C:/Videos"), (1, "video2.mp4", "C:/Videos")]
            # selected_rows = {0, 1}
        """
        selected_rows = set(idx.row() for idx in self.file_table.selectionModel().selectedRows())
        files = []
        for row in selected_rows:
            filename = self.file_table.item(row, 0).text()
            folder = self.file_table.item(row, 1).text()
            files.append((row, filename, folder))
        return files, selected_rows

    def clear_list(self):
        """Clear the file list"""
        self.file_table.setRowCount(0)

class DragDropTable(QTableWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setItemDelegate(FontDelegate(font_size=8))
        self.setAcceptDrops(True)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['Filename', 'Path', 'Duration', 'Size', 'Status'])

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)

        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 80)
        self.setColumnWidth(4, 80)

        header.setDefaultAlignment(Qt.AlignCenter)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.showGrid = True

        rows_to_show = 10
        row_height = self.verticalHeader().defaultSectionSize()
        header_height = self.horizontalHeader().height()
        total_height = row_height * rows_to_show + header_height + 1
        self.setMinimumHeight(total_height)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

            filepaths = [url.toLocalFile() for url in event.mimeData().urls() if os.path.isfile(url.toLocalFile())]
            self.files_dropped.emit(filepaths)

        else:
            event.ignore()

    def add_file(self, filename, inputfile_folder, duration_str, size_str):
        for row in range(self.rowCount()):
            if self.item(row, 0).text() == filename and self.item(row, 1).text() == inputfile_folder:
                return
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(filename))
        self.setItem(row, 1, QTableWidgetItem(inputfile_folder))

        d_item = QTableWidgetItem(duration_str)
        d_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 2, d_item)

        size_item = QTableWidgetItem(size_str)
        size_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 3, size_item)

        self.setItem(row, 4, QTableWidgetItem(""))
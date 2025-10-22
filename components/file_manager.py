from PyQt5.QtWidgets import (
    QTableWidgetItem, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, QCoreApplication, Qt, 
    QObject, pyqtSignal, QUrl)
from PyQt5.QtGui import QPixmap, QDesktopServices
import os
from utils import resource_path
from .delegate import FontDelegate
import json
import subprocess
import sys

class FileManager(QObject):
    log_signal = pyqtSignal(str)  # For logging messages

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.file_table = DragDropTable()
        self.file_loader_thread = None
        self.setup_file_table()

    def setup_file_table(self):
        self.file_table.itemDoubleClicked.connect(self.open_file_on_doubleclick)
        self.file_table.files_dropped.connect(self.start_loading_files)

    def get_widget(self):
        return self.file_table

    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "Select files",
            "",
            "All files (*)"
        )
        if files:
            self.start_loading_files(files)

    def start_loading_files(self, file_list):
        if self.file_loader_thread is not None and self.file_loader_thread.isRunning():
            self.log_signal.emit("File loading already in progress. Please wait.")
            return
        self.file_loader_thread = FileLoaderThread(file_list)
        self.file_loader_thread.log_signal.connect(self.log_signal.emit)
        self.file_loader_thread.add_file_signal.connect(self.on_add_file_received)
        self.file_loader_thread.start()

    def on_add_file_received(self, filename, folder, duration_str, size_str):
        self.file_table.add_file(filename, folder, duration_str, size_str)

    def open_file_on_doubleclick(self, item):
        row = item.row()
        filename = self.file_table.item(row, 0).text()
        folder = self.file_table.item(row, 1).text()
        full_path = os.path.join(folder, filename)
        url = QUrl.fromLocalFile(full_path)
        if not QDesktopServices.openUrl(url):
            self.log_signal.emit(f"Cannot open file: {full_path}")

    def update_status(self, row, status):
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
                - list: List of tuples (row_number, filename, folder) for each selected file
                - set: Set of selected row indices
            
        Example:
            files, selected_rows = file_manager.get_selected_files()
            # files = [(0, "video1.mp4", "C:/Videos"), (1, "video2.mp4", "C:/Videos")]
            # selected_rows = {0, 1}
        """
        selected_rows = set(idx.row() for idx in self.file_table.selectionModel().selectedRows())
        files = []
        for row_number in selected_rows:
            filename = self.file_table.item(row_number, 0).text()
            folder = self.file_table.item(row_number, 1).text()
            files.append((row_number, filename, folder))
        return files, selected_rows

    def remove_selected_files(self):
        selected_files, _ = self.get_selected_files()
        for row_number, file_name, _ in sorted(selected_files, key=lambda x: x[0], reverse=True):
            self.file_table.removeRow(row_number)
            self.log_signal.emit(f"Removed {file_name}.")

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
        # align center for duration and size columns
        header.setDefaultAlignment(Qt.AlignCenter)
        # disable auto bold for header sections when select a item
        header.setHighlightSections(False)

        self.setColumnWidth(2, 90)
        self.setColumnWidth(3, 80)
        self.setColumnWidth(4, 80)

        # select entire row when clicked on an item
        self.setSelectionBehavior(QTableWidget.SelectRows)
        # disable editing when double-clicked on item
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        # show grid lines
        self.showGrid = True

        # set minimum height to show 9 rows
        rows_to_show = 5
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

class FileLoaderThread(QThread):
    log_signal = pyqtSignal(str)
    add_file_signal = pyqtSignal(str, str, str, str)

    def __init__(self, filepaths):
        super().__init__()
        self.filepaths = filepaths
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True

    def run(self):
        total = len(self.filepaths)
        for idx, filepath in enumerate(self.filepaths):
            if self._is_stopped:
                break

            filename = os.path.basename(filepath)
            folder = os.path.dirname(filepath)
            filesize = format_size(os.path.getsize(filepath))

            duration_sec = self.get_duration(filepath)
            duration_str = format_duration(duration_sec)

            self.log_signal.emit(f"{idx + 1}/{total}: {filename}, Duration: {duration_str}, Size: {filesize}")
            self.add_file_signal.emit(filename, folder, duration_str, filesize)
            QCoreApplication.processEvents()

    def get_duration(self, filepath):
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                check=True,
                startupinfo=startupinfo
            )
            metadata = json.loads(result.stdout)
            return float(metadata['format']['duration'])
        except Exception:
            return None


def format_duration(seconds):
    if seconds is None:
        return "N/A"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB")
    i = 0
    p = 1024
    while size_bytes >= p and i < len(size_name) - 1:
        size_bytes /= p
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"
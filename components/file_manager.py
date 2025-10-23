from PyQt5.QtWidgets import (
    QTableWidgetItem, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, QCoreApplication, Qt, 
    QObject, pyqtSignal, QUrl)
from PyQt5.QtGui import QPixmap, QDesktopServices, QIcon
import os
from utils import resource_path
from enum import Enum
from .delegate import FontDelegate
import json
import subprocess
import sys

class FileInfo:
    def __init__(self, filepath: str, metadata: dict):
        self._filepath = filepath
        self._metadata = metadata
        self._info = self._get_info_from_metadata()

    def _get_info_from_metadata(self):
        format_info = self._metadata.get('format', {})
        
        streams = self._metadata.get('streams', [])
        video_stream = next((stream for stream in streams if stream.get('codec_type') == 'video'), None)
        return {
            "duration": format_info.get('duration'),
            "size": format_info.get('size'),
            "video_stream": {
                "codec": video_stream.get('codec_name'),
                "width": video_stream.get('width'),
                "height": video_stream.get('height'),
                "bitrate": video_stream.get('bit_rate')
            } if video_stream else None
        }

    @property
    def filename(self) -> str:
        return os.path.basename(self._filepath)

    @property
    def folder(self) -> str:
        return os.path.dirname(self._filepath)

    @property
    def resolution(self) -> str:
        if self._info.get("video_stream"):
            width = self._info["video_stream"]["width"]
            height = self._info["video_stream"]["height"]
            if width and height:
                return f'{width}x{height}'
        return "N/A"

    @property
    def codec(self) -> str:
        if self._info.get("video_stream"):
            return self._info["video_stream"].get("codec", "N/A")
        return "N/A"

    @property
    def bitrate(self) -> str:
        if self._info.get("video_stream"):
            bitrate_val = self._info["video_stream"].get("bitrate")
            if bitrate_val:
                try:
                    bitrate_val = float(bitrate_val)
                    if bitrate_val < 0: return "N/A"
                    kbps = bitrate_val / 1000
                    return f"{kbps / 1000:.2f} Mbps" if kbps >= 1000 else f"{kbps:.1f} kbps"
                except (ValueError, TypeError):
                    return "N/A"
        return "N/A"

    @property
    def duration(self) -> str:
        seconds = self._info.get("duration")
        if seconds:
            try:
                seconds = float(seconds)
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            except (ValueError, TypeError):
                return "N/A"
        return "N/A"

    @property
    def size(self) -> str:
        size_bytes = self._info.get("size")
        if size_bytes:
            try:
                size_bytes_float = float(size_bytes)
                if size_bytes_float == 0: return "0B"
                size_name = ("B", "KB", "MB", "GB")
                size_bytes_int = int(size_bytes_float)
                i = int(abs(size_bytes_int).bit_length() - 1) // 10 if size_bytes_int > 0 else 0
                return f"{size_bytes_float / (1024**i):.2f} {size_name[i]}"
            except (ValueError, TypeError):
                return "N/A"
        return "N/A"

class FileManager(QObject):
    log_signal = pyqtSignal(str)

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
        self.file_loader_thread.add_file_signal.connect(self._on_add_file)
        self.file_loader_thread.progress_signal.connect(self._on_loading_progress)
        self.file_loader_thread.finished.connect(self._on_loading_finished)
        self.file_loader_thread.start()

    def _on_add_file(self, file_info):
        self.file_table.add_file(file_info)

    def _on_loading_finished(self):
        """Cleans up the file loader thread after it has finished."""
        self.log_signal.emit("Finished loading file information.")
        self.file_loader_thread.deleteLater()
        self.file_loader_thread = None

    def _on_loading_progress(self, current, total, filename):
        """Updates the log with file loading progress."""
        self.log_signal.emit(f"{current}/{total} - {filename}")

    def open_file_on_doubleclick(self, item):
        row = item.row()

        filename_item = self.file_table.item(row, self.file_table.Column.FILENAME.value)
        folder_item = self.file_table.item(row, self.file_table.Column.PATH.value)

        if not (filename_item and folder_item):
            self.log_signal.emit(f"Error: Could not retrieve file info for row {row}.")
            return

        filename = filename_item.text()
        folder = folder_item.text()
        full_path = os.path.join(folder, filename)

        if not os.path.exists(full_path):
            self.log_signal.emit(f"File not found: {full_path}")
            return

        url = QUrl.fromLocalFile(full_path)
        if not QDesktopServices.openUrl(url):
            self.log_signal.emit(f"Cannot open file: {full_path}")

    def update_status(self, row, status):
        """Updates the status icon and tooltip for a given row."""
        icon_map = {
            "Processing": resource_path("icon/processing.png"),
            "Failed": resource_path("icon/failed.png"),
            "Success": resource_path("icon/success.png"),
            "Successed": resource_path("icon/success.png"), # Handle old value for compatibility
            "Pending": resource_path("icon/pending.png"),
            "Stopped": resource_path("icon/stop.png"),
        }

        # Remove old status (widget, text, icon)
        self.file_table.removeCellWidget(row, self.file_table.Column.STATUS.value)
        item = self.file_table.item(row, self.file_table.Column.STATUS.value)
        if item:
            item.setText("")
            item.setIcon(QIcon())

        if status in icon_map:
            # QLabel to hold the centered icon. This trick can center icon in column
            label = QLabel()
            pixmap = QPixmap(icon_map[status])
            pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.setToolTip(status.replace("Successed", "Success"))
            self.file_table.setCellWidget(row, self.file_table.Column.STATUS.value, label)

    def get_selected_files(self):
        selected_rows = {idx.row() for idx in self.file_table.selectionModel().selectedRows()}
        files = []
        for row_number in selected_rows:
            filename_item = self.file_table.item(row_number, self.file_table.Column.FILENAME.value)
            folder_item = self.file_table.item(row_number, self.file_table.Column.PATH.value)

            if filename_item and folder_item:
                filename = filename_item.text()
                folder = folder_item.text()
                files.append((row_number, filename, folder))
            else:
                self.log_signal.emit(f"Warning: Could not retrieve file info for row {row_number}. Skipping.")

        return files, selected_rows

    def remove_selected_files(self):
        """Removes all selected rows from the file table."""
        # Get all selected row indices directly from the selection model
        selected_rows = self.file_table.selectionModel().selectedRows()
        
        # Sort row indices in reverse order to avoid index shifting issues during removal
        for index in sorted(selected_rows, key=lambda idx: idx.row(), reverse=True):
            filename = self.file_table.item(index.row(), self.file_table.Column.FILENAME.value).text()
            self.file_table.removeRow(index.row())
            self.log_signal.emit(f"Removed {filename}.")

class DragDropTable(QTableWidget):
    files_dropped = pyqtSignal(list)

    class Column(Enum):
        FILENAME = 0
        PATH = 1
        RESOLUTION = 2
        CODEC = 3
        BITRATE = 4
        DURATION = 5
        SIZE = 6
        STATUS = 7

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_ui()
        self._setup_behavior()

    def _setup_ui(self):
        """Sets up the main UI components of the table."""
        self.setItemDelegate(FontDelegate(font_size=8))
        self.setColumnCount(len(self.Column))
        self._setup_headers()
        self.showGrid()

        # Set a dynamic minimum height to show a certain number of rows
        rows_to_show = 5
        row_height = self.verticalHeader().defaultSectionSize()
        header_height = self.horizontalHeader().height()
        total_height = row_height * rows_to_show + header_height + 1
        self.setMinimumHeight(total_height)

    def _setup_headers(self):
        """Configures the table headers."""
        self.setHorizontalHeaderLabels([col.name.replace('_', ' ').title() for col in self.Column])
        header = self.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setHighlightSections(False)

        # Dynamic columns
        header.setSectionResizeMode(self.Column.FILENAME.value, QHeaderView.Stretch)
        header.setSectionResizeMode(self.Column.PATH.value, QHeaderView.Stretch)

        # Fixed width columns
        fixed_widths = {
            self.Column.RESOLUTION: 100, self.Column.CODEC: 70, self.Column.BITRATE: 80,
            self.Column.DURATION: 80, self.Column.SIZE: 80, self.Column.STATUS: 60
        }
        for col, width in fixed_widths.items():
            header.setSectionResizeMode(col.value, QHeaderView.Fixed)
            self.setColumnWidth(col.value, width)

    def _setup_behavior(self):
        """Configures table interaction behavior."""
        self.setAcceptDrops(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

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

    def _create_table_item(self, text: str, alignment: Qt.AlignmentFlag = Qt.AlignVCenter | Qt.AlignLeft) -> QTableWidgetItem:
        """Creates a QTableWidgetItem with specified text and alignment."""
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item

    def add_file(self, file_info: FileInfo):
        """Adds a new file to the table, avoiding duplicates."""
        # Check duplicate
        for row in range(self.rowCount()):
            filename_item = self.item(row, self.Column.FILENAME.value)
            path_item = self.item(row, self.Column.PATH.value)
            if filename_item and path_item:
                if filename_item.text() == file_info.filename and path_item.text() == file_info.folder:
                    return

        row = self.rowCount()
        self.insertRow(row)

        self.setItem(row, self.Column.FILENAME.value, self._create_table_item(file_info.filename))
        self.setItem(row, self.Column.PATH.value, self._create_table_item(file_info.folder))
        self.setItem(row, self.Column.RESOLUTION.value, self._create_table_item(file_info.resolution, Qt.AlignCenter))
        self.setItem(row, self.Column.CODEC.value, self._create_table_item(file_info.codec, Qt.AlignCenter))
        self.setItem(row, self.Column.BITRATE.value, self._create_table_item(file_info.bitrate, Qt.AlignCenter))
        self.setItem(row, self.Column.DURATION.value, self._create_table_item(file_info.duration, Qt.AlignCenter))
        self.setItem(row, self.Column.SIZE.value, self._create_table_item(file_info.size, Qt.AlignCenter))
        self.setItem(row, self.Column.STATUS.value, self._create_table_item("", Qt.AlignCenter))

class FileLoaderThread(QThread):
    log_signal = pyqtSignal(str)
    add_file_signal = pyqtSignal(FileInfo) 
    progress_signal = pyqtSignal(int, int, str)

    def __init__(self, input_files: list[str]):
        super().__init__()
        self.input_files = input_files
        self._is_stopped = False

    def stop(self):
        """Sets a flag to gracefully stop the thread's execution."""
        self._is_stopped = True

    def run(self):
        """The main execution method of the thread."""
        # Check for ffprobe existence once before starting the loop.
        if not self.is_ffprobe_available():
            self.log_signal.emit("Error: ffprobe not found. Please ensure ffmpeg is in your system's PATH.")
            return

        total = len(self.input_files)
        for idx, filepath in enumerate(self.input_files):
            if self._is_stopped:
                break

            self.progress_signal.emit(idx + 1, total, os.path.basename(filepath))

            ffprobe_output = self.run_ffprobe(filepath)
            if not ffprobe_output:
                self.log_signal.emit(f"Failed to get info for file: {filepath}")
                continue

            file_info = FileInfo(filepath, ffprobe_output)
            self.add_file_signal.emit(file_info)

    def run_ffprobe(self, filepath: str) -> dict | None:
        """Executes ffprobe on a given file to extract media information.
            Args:
                filepath (str): The absolute path to the media file to be analyzed.

            Returns:
                dict | None: A dictionary containing the parsed JSON output from
                            ffprobe if successful, otherwise None.
        """
        try:
            startupinfo = subprocess.STARTUPINFO() if sys.platform == "win32" else None
            if startupinfo: startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                check=True,
                startupinfo=startupinfo
            )
            return json.loads(result.stdout)
        except Exception as e:
            self.log_signal.emit(f"Error running ffprobe for {filepath}: {e}")
            return None

    @staticmethod
    def is_ffprobe_available() -> bool:
        """Checks if ffprobe command is available in the system's PATH."""
        from shutil import which
        return which('ffprobe') is not None
from PyQt5.QtWidgets import (
    QTableWidgetItem, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QApplication
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, QStandardPaths, Qt, 
    QObject, pyqtSignal, QUrl)
from PyQt5.QtGui import QPixmap, QDesktopServices, QIcon
import os
from enum import Enum
import json
import subprocess
import sys

from helper import resource_path, FontDelegate, styled_text

class FileInfo:
    """A data class to store and process media file information.

    This class is initialized with a file path and the raw JSON output
    from ffprobe. It provides properties to access formatted media
    attributes like resolution, codec, duration, etc., encapsulating
    the logic for parsing and formatting this information.
    """
    def __init__(self, filepath: str, metadata: dict):
        """Initializes the FileInfo object.

        Args:
            filepath (str): The absolute path to the media file.
            metadata (dict): The raw JSON output from an ffprobe analysis.
        """
        self._filepath = filepath
        self._metadata = metadata
        self._info = self._parse_metadata()

    def _parse_metadata(self):
        """Parses the raw ffprobe metadata to extract key information."""
        format_info = self._metadata.get('format', {})
        
        streams = self._metadata.get('streams', [])
        video_stream = next((stream for stream in streams if stream.get('codec_type') == 'video'), None)
        return {
            "duration": format_info.get('duration'),
            "size": format_info.get('size'),
            "bitrate": format_info.get('bit_rate'),
            "video_stream": {
                "codec": video_stream.get('codec_name'),
                "width": video_stream.get('width'),
                "height": video_stream.get('height'),
                "bitrate": video_stream.get('bit_rate')
            } if video_stream else None
        }

    @property
    def filename(self) -> str:
        """Returns the base name of the file."""
        return os.path.basename(self._filepath)

    @property
    def folder(self) -> str:
        """Returns the directory path of the file."""
        return os.path.dirname(self._filepath)

    @property
    def resolution(self) -> str:
        """Returns the video resolution as a 'widthxheight' string.

        Returns:
            str: The formatted resolution string (e.g., "1920x1080"),
                 or "N/A" if not available.
        """
        if self._info.get("video_stream"):
            width = self._info["video_stream"]["width"]
            height = self._info["video_stream"]["height"]
            if width and height:
                return f'{width}x{height}'
        return "N/A"

    @property
    def codec(self) -> str:
        """Returns the name of the video codec.

        Returns:
            str: The codec name (e.g., "h264"), or "N/A" if not available.
        """
        if self._info.get("video_stream"):
            return self._info["video_stream"].get("codec", "N/A")
        return "N/A"

    @property
    def bitrate(self) -> str:
        """Returns the video bitrate, formatted in kbps or Mbps.

        Returns:
            str: The formatted bitrate string (e.g., "800.5 kbps" or
                 "1.50 Mbps"), or "N/A" if not available or invalid.
        """
        if self._info.get("video_stream"):
            # bitrate_val = self._info["video_stream"].get("bitrate") # get bitrate in stream dict
            bitrate_val = self._info.get("bitrate") # get bitrate in format dict
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
        """Returns the media duration formatted as HH:MM:SS.

        Returns:
            str: The formatted duration string (e.g., "00:10:32"),
                 or "N/A" if not available.
        """
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
        """Returns the file size, formatted in B, KB, MB, or GB.

        Returns:
            str: The formatted file size string (e.g., "1.23 GB"),
                 or "N/A" if not available.
        """
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
    """Manages the file list, loading operations, and user interactions.

    This class acts as a controller for the file table. It handles adding
    files (via dialog or drag-drop), loading their metadata in a background
    thread, and updating their status during processing.
    """
    log_signal = pyqtSignal(str)

    def __init__(self, parent):
        """Initializes the FileManager."""
        super().__init__()
        self.parent = parent
        self.file_table = DragDropTable()
        self.file_loader_thread = None
        self._setup_file_table()

    def _setup_file_table(self):
        """Sets up signal-slot connections for the file table."""
        self.file_table.itemDoubleClicked.connect(self.open_file_on_doubleclick)
        self.file_table.files_dropped.connect(self.start_loading_files)

    def _add_file_to_table(self, file_info: FileInfo):
        """Slot to receive a FileInfo object and add it to the table."""
        self.file_table.add_file(file_info)

    def _on_loading_finished(self):
        """Cleans up the file loader thread after it has finished."""
        self.log_signal.emit(styled_text('bold', 'blue', None, "Finished loading file information."))
        self.file_loader_thread.deleteLater()
        self.file_loader_thread = None

    def _update_loading_progress(self, current: int, total: int, filename: str):
        """Updates the log with file loading progress."""
        self.log_signal.emit(styled_text(None, None, None, f"{current}/{total} - {filename}"))

    def get_widget(self):
        """Returns the underlying QTableWidget instance."""
        return self.file_table

    def add_files_dialog(self):
        """Opens a file dialog to allow the user to select one or more files."""
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)
        default_dir = "C:/Users/lamdv/Videos/Love.in.the.Clouds/mp4/output"
        files, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "Select files",
            default_dir,
            "All files (*)"
        )
        if files:
            self.start_loading_files(files)

    def start_loading_files(self, file_list):
        """Starts a background thread to load information for a list of files.

        Args:
            file_list (list[str]): A list of absolute file paths to process.
        """
        if self.file_loader_thread is not None and self.file_loader_thread.isRunning():
            self.log_signal.emit(styled_text('bold', 'blue', None, "File loading already in progress. Please wait."))
            return
        self.file_loader_thread = FileLoaderThread(file_list)
        self.file_loader_thread.log_signal.connect(self.log_signal.emit)
        self.file_loader_thread.add_file_signal.connect(self._add_file_to_table)
        self.file_loader_thread.progress_signal.connect(self._update_loading_progress)
        self.file_loader_thread.finished.connect(self._on_loading_finished)
        self.file_loader_thread.start()

    def open_file_on_doubleclick(self, item):
        """Opens the file with the default system application when double-clicked.

        Args:
            item (QTableWidgetItem): The table item that was double-clicked.
        """
        row = item.row()

        filename_item = self.file_table.item(row, self.file_table.Column.FILENAME.value)
        folder_item = self.file_table.item(row, self.file_table.Column.PATH.value)

        if not (filename_item and folder_item):
            self.log_signal.emit(styled_text('bold', 'red', None, f"Error: Could not retrieve file info for row {row}."))
            return

        filename = filename_item.text()
        folder = folder_item.text()
        full_path = os.path.join(folder, filename)

        if not os.path.exists(full_path):
            self.log_signal.emit(styled_text('bold', 'red', None, f"File not found: {full_path}"))
            return

        url = QUrl.fromLocalFile(full_path)
        if not QDesktopServices.openUrl(url):
            self.log_signal.emit(styled_text('bold', 'red', None, f"Cannot open file: {full_path}"))

    def update_status(self, row, status):
        """Updates the status icon in the table for a given row.

        Args:
            row (int): The row index to update.
            status (str): The new status (e.g., "Processing", "Success", "Failed").
        """
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
        """Gets the data for all currently selected files in the table.

        Returns:
            tuple: A tuple containing:
                - list: A list of tuples, where each tuple is (row_index, filename, folder).
                - set: A set of selected row indices.
        """
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
                self.log_signal.emit(styled_text('bold', 'blue', None, f"Could not retrieve file info for row {row_number}. Skipping."))

        return files, selected_rows

    def remove_selected_files(self):
        """Removes all selected rows from the file table."""
        # Get all selected row indices directly from the selection model
        selected_rows = self.file_table.selectionModel().selectedRows()
        
        # Sort row indices in reverse order to avoid index shifting issues during removal
        for index in sorted(selected_rows, key=lambda idx: idx.row(), reverse=True):
            filename = self.file_table.item(index.row(), self.file_table.Column.FILENAME.value).text()
            self.file_table.removeRow(index.row())
            self.log_signal.emit(styled_text('bold', 'blue', None, f"Removed {filename}."))

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
        """Initializes the DragDropTable widget.

        Args:
            *args: Variable length argument list for QTableWidget.
            **kwargs: Arbitrary keyword arguments for QTableWidget.
        """
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
        # Allow selecting multiple items by dragging the mouse
        self.setSelectionMode(QTableWidget.ExtendedSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def _create_table_item(self, text: str, alignment: Qt.AlignmentFlag = Qt.AlignVCenter | Qt.AlignLeft) -> QTableWidgetItem:
        """Creates a QTableWidgetItem with specified text and alignment."""
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item

    # Note: The following event handlers (dragEnterEvent, dragMoveEvent, dropEvent,
    # contextMenuEvent) must use camelCase naming because they are overriding
    # methods from the parent QWidget class. This is a requirement of PyQt.

    def dragEnterEvent(self, event):
        """Handles the drag enter event to accept file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handles the drag move event to accept file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handles the drop event to process dropped files."""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            filepaths = [url.toLocalFile() for url in event.mimeData().urls() if os.path.isfile(url.toLocalFile())]
            self.files_dropped.emit(filepaths)
        else:
            event.ignore()

    def contextMenuEvent(self, event):
        """Shows a context menu on right-click."""
        item = self.itemAt(event.pos())
        if not item:
            return

        row = item.row()
        filename_item = self.item(row, self.Column.FILENAME.value)
        path_item = self.item(row, self.Column.PATH.value)

        if not (filename_item and path_item):
            return

        menu = QMenu(self)
        copy_filename_action = menu.addAction("Copy Filename")
        copy_path_action = menu.addAction("Copy Path")

        action = menu.exec_(event.globalPos())

        clipboard = QApplication.clipboard()
        if action == copy_filename_action:
            clipboard.setText(filename_item.text())
        elif action == copy_path_action:
            clipboard.setText(path_item.text())
    
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
    """A QThread worker for loading and processing media file information.

    This thread processes a list of file paths in the background to avoid
    freezing the main application UI. For each file, it executes `ffprobe`
    to extract media metadata, creates a `FileInfo` object, and emits signals
    to update the UI with progress and results.
    """
    log_signal = pyqtSignal(str)
    add_file_signal = pyqtSignal(FileInfo) 
    progress_signal = pyqtSignal(int, int, str)

    def __init__(self, input_files: list[str]):
        """Initializes the FileLoaderThread.

        Args:
            input_files (list[str]): A list of absolute file paths to be processed.
        """
        super().__init__()
        self.input_files = input_files
        self._is_stopped = False

    def _run_ffprobe(self, filepath: str) -> dict | None:
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
            self.log_signal.emit(styled_text('bold', 'red', None, f"Error running ffprobe for {filepath}: {e}"))
            return None

    @staticmethod
    def _is_ffprobe_available() -> bool:
        """Checks if ffprobe command is available in the system's PATH."""
        from shutil import which
        return which('ffprobe') is not None
    
    def stop(self):
        """Sets a flag to gracefully stop the thread's execution."""
        self._is_stopped = True

    def run(self):
        """The main execution method of the thread."""
        # Check for ffprobe existence once before starting the loop.
        if not self._is_ffprobe_available():
            self.log_signal.emit(styled_text('bold', 'red', None, "Error: ffprobe not found. Please ensure ffmpeg is in your system's PATH."))
            return

        total = len(self.input_files)
        for idx, filepath in enumerate(self.input_files):
            if self._is_stopped:
                break

            self.progress_signal.emit(idx + 1, total, os.path.basename(filepath))

            ffprobe_output = self._run_ffprobe(filepath)
            if not ffprobe_output:
                self.log_signal.emit(styled_text('bold', 'red', None, f"Failed to get info for file: {filepath}"))
                continue

            file_info = FileInfo(filepath, ffprobe_output)
            self.add_file_signal.emit(file_info)

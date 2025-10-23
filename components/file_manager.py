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
        self.file_loader_thread.add_file_signal.connect(self.file_table.add_file)
        self.file_loader_thread.start()

    # def on_add_file_received(self, file_info: FileInfo):
    #     """Slot to receive FileInfo object and add it to the table."""
    #     self.file_table.add_file(file_info)

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
            old_widget = self.file_table.cellWidget(row, 7)
            if old_widget:
                self.file_table.removeCellWidget(row, 7)
            self.file_table.setCellWidget(row, 7, label)
        elif status == "" or status is None:
            old_widget = self.file_table.cellWidget(row, 7)
            if old_widget:
                self.file_table.removeCellWidget(row, 7)
            self.file_table.setItem(row, 7, QTableWidgetItem(""))
        else:
            old_widget = self.file_table.cellWidget(row, 7)
            if old_widget:
                self.file_table.removeCellWidget(row, 7)
            item = QTableWidgetItem(status)
            item.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 7, item)

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
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(['Filename', 'Path', 'Resolution', 'Codec', 'Bit rate' ,'Duration', 'Size', 'Status'])

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        # align center for duration and size columns
        header.setDefaultAlignment(Qt.AlignCenter)
        # disable auto bold for header sections when select a item
        header.setHighlightSections(False)

        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 70)
        self.setColumnWidth(4, 80)
        self.setColumnWidth(5, 80)
        self.setColumnWidth(6, 80)
        self.setColumnWidth(7, 60)


        # select entire row when clicked on an item
        self.setSelectionBehavior(QTableWidget.SelectRows)
        # disable editing when double-clicked on item
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        # show grid lines
        self.showGrid = True

        # set minimum height
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

    def set_item(self, row, column, item, align):
        item = QTableWidgetItem(item)
        match align:
            case "center":
                item.setTextAlignment(Qt.AlignCenter)
            case "left":
                item.setTextAlignment(Qt.AlignLeft)
            case "right":
                item.setTextAlignment(Qt.AlignRight)
        super().setItem(row, column, item)

    def add_file(self, file_info: FileInfo):
        for row in range(self.rowCount()):
            if self.item(row, 0).text() == file_info.filename and self.item(row, 1).text() == file_info.folder:
                return
        row = self.rowCount()
        self.insertRow(row)

        self.set_item(row, 0, file_info.filename, "left")
        self.set_item(row, 1, file_info.folder, "left")
        self.set_item(row, 2, file_info.resolution, "center")
        self.set_item(row, 3, file_info.codec, "center")
        self.set_item(row, 4, file_info.bitrate, "center")
        self.set_item(row, 5, file_info.duration, "center")
        self.set_item(row, 6, file_info.size, "center")
        self.set_item(row, 7, "", "center")

class FileLoaderThread(QThread):
    log_signal = pyqtSignal(str)
    add_file_signal = pyqtSignal(FileInfo) 

    def __init__(self, input_files):
        super().__init__()
        self.input_files = input_files
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True

    def run(self):
        total = len(self.input_files)
        for idx, filepath in enumerate(self.input_files):
            if self._is_stopped:
                break

            ffprobe_output = self.run_ffprobe(filepath)
            if not ffprobe_output:
                self.log_signal.emit(f"Failed to get info for file: {filepath}")
                continue
            else:
                self.log_signal.emit(f"{idx+1}/{total} - {filepath}")

            file_info = FileInfo(filepath, ffprobe_output)
            self.add_file_signal.emit(file_info)
            QCoreApplication.processEvents()

    def run_ffprobe(self, file):
        """Executes ffprobe on a given file to extract media information.
            Args:
                file (str): The absolute path to the media file to be analyzed.

            Returns:
                dict | None: A dictionary containing the parsed JSON output from
                            ffprobe if successful, otherwise None.
        """
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                check=True,
                startupinfo=startupinfo
            )
            return json.loads(result.stdout)
        except FileNotFoundError:
            self.log_signal.emit("ffprobe not found. Please ensure ffmpeg is in your system's PATH.")
            return None
        except Exception as e:
            self.log_signal.emit(f"Error running ffprobe for {file}: {e}")
            return None
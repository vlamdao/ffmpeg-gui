import os
import json
import subprocess
import sys
from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication

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


import os
import tempfile
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from processor import FFmpegWorker

class ThumbnailProcessor(QObject):
    """
    Handles the background processing for setting a video thumbnail using FFmpeg.
    """
    log_signal = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str) # success (bool), status_message (str)

    def __init__(self, parent=None):
        """Initializes the ThumbnailProcessor."""
        super().__init__(parent)
        self._worker: FFmpegWorker | None = None
        self._temp_thumb_path: str | None = None

    def is_running(self) -> bool:
        """Checks if a thumbnail process is currently active."""
        return self._worker is not None and self._worker.isRunning()

    def start(self, video_path: str, output_path: str, timestamp: str):
        """Starts the process of setting the thumbnail."""
        if self.is_running():
            self.log_signal.emit("Thumbnail processing is already in progress.")
            return

        try:
            commands, self._temp_thumb_path = self._create_commands(video_path, output_path, timestamp)
            self._start_worker(commands)
            self.log_signal.emit(f"Setting thumbnail for '{os.path.basename(video_path)}' at {timestamp}...")
        except Exception as e:
            error_msg = f"Could not start thumbnail process: {e}"
            self.log_signal.emit(f"Error preparing thumbnail job: {e}")
            self.processing_finished.emit(False, error_msg)

    def _create_commands(self, video_path: str, output_path: str, timestamp: str) -> tuple[list[str], str]:
        """Creates the FFmpeg commands for extracting and embedding a thumbnail."""
        filename = os.path.basename(video_path)
        thumb_fd, thumb_path = tempfile.mkstemp(suffix=".jpg", prefix=f"{filename}_thumb_")
        os.close(thumb_fd)

        os.makedirs(output_path, exist_ok=True)
        output_file_path = os.path.join(output_path, filename)

        cmd1 = (f'ffmpeg -y -loglevel warning -ss {timestamp} -i "{video_path}" '
                f'-frames:v 1 "{thumb_path}"')

        cmd2 = (f'ffmpeg -y -loglevel warning -i "{video_path}" -i "{thumb_path}" '
                f'-map 0 -map 1 -c copy -disposition:v:1 attached_pic "{output_file_path}"')
        
        return [cmd1, cmd2], thumb_path

    def _start_worker(self, commands: list[str]):
        """Initializes and starts the FFmpegWorker."""
        job = (-1, commands) # Use -1 for row_index as this is a single job
        self._worker = FFmpegWorker([job])
        self._worker.log_signal.connect(self.log_signal)
        self._worker.update_status.connect(self._on_worker_status_update)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.start()

    @pyqtSlot(int, str)
    def _on_worker_status_update(self, row_index: int, status: str):
        """Handles status updates from the worker and emits the final result."""
        # We only care about the final status, not "Processing"
        if status in ("Success", "Failed", "Stopped"):
            is_success = (status == "Success")
            if is_success:
                status_message = "Thumbnail has been set successfully."
            else:
                status_message = f"Failed to set thumbnail. Status: {status}"
            self.processing_finished.emit(is_success, status_message)

    def _on_worker_thread_finished(self):
        """Cleans up resources after the worker thread has completely finished."""
        if self._temp_thumb_path and os.path.exists(self._temp_thumb_path):
            os.remove(self._temp_thumb_path)
        
        self._worker = None
        self._temp_thumb_path = None
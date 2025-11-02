import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from processor import FFmpegWorker
from .command import CommandTemplates
from helper import bold_green, bold_red, bold_yellow, bold_blue

class Processor(QObject):
    """
    Handles the background processing for setting a video thumbnail using FFmpeg.
    """
    log_signal = pyqtSignal(str)
    processing_finished = pyqtSignal()

    def __init__(self, parent=None):
        """Initializes the Processor."""
        super().__init__(parent)
        self._worker: FFmpegWorker | None = None
        self._temp_thumb_path: str | None = None

    def is_running(self) -> bool:
        """Checks if a thumbnail process is currently active."""
        return self._worker is not None and self._worker.isRunning()

    def start(self, video_path: str, output_folder: str, timestamp: str):
        """Starts the process of setting the thumbnail."""
        if self.is_running():
            self.log_signal.emit(bold_yellow("Thumbnail processing is already in progress."))
            return
        try:
            command_template = CommandTemplates(video_path, output_folder, timestamp)
            commands, self._temp_thumb_path = command_template.generate_commands()
            self._start_worker(commands)
            self.log_signal.emit(bold_blue(f"Setting thumbnail for '{os.path.basename(video_path)}' at {timestamp}..."))
        except Exception as e:
            self.log_signal.emit(bold_red(f'Error: {e}'))
            self.processing_finished.emit()

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
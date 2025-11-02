import os
from typing import TYPE_CHECKING
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from processor import FFmpegWorker
from helper import styled_text

class VideoJoinerProcessor(QObject):
    """
    Handles the background processing for joining videos using FFmpeg.
    """
    log_signal = pyqtSignal(str)
    processing_finished = pyqtSignal()

    if TYPE_CHECKING:
        from .command import CommandTemplate

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: FFmpegWorker | None = None
        self._temp_concat_file_path: str | None = None

    def is_running(self) -> bool:
        """Checks if a join process is currently active."""
        return self._worker is not None and self._worker.isRunning()

    def start(self, 
              selected_files: list[tuple[int, str, str]], 
              output_folder: str, 
              cmd_template: 'CommandTemplate', 
              join_method: str):
        """Starts the process of joining videos."""
        if self.is_running():
            self.log_signal.emit(styled_text('bold', 'blue', None, "Join processVideo joining is already in progress."))
            return

        try:
            command, self._temp_concat_file_path = cmd_template.generate_command(selected_files, output_folder, join_method)
            if not command:
                raise ValueError("Command template is empty or failed to generate.")

            self._start_worker(command)
            self.log_signal.emit(styled_text('bold', 'blue', None, f"Starting to join {len(selected_files)} files..."))
        except Exception as e:
            self.log_signal.emit(styled_text('bold', 'red', None, f'Error: Could not start join process: {e}'))
            self.processing_finished.emit()
            self._cleanup()

    def _start_worker(self, command: str):
        """Initializes and starts the FFmpegWorker."""
        job = (-1, [command])  # Use -1 for row_index as this is a single job
        self._worker = FFmpegWorker([job])
        self._worker.log_signal.connect(self.log_signal)
        self._worker.update_status.connect(self._on_worker_status_update)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.start()

    def stop(self):
        """Stops the running worker thread."""
        if self.is_running():
            self._worker.stop_all()
            self.log_signal.emit(styled_text('bold', 'blue', None, "Join process stopped by user."))
            self.processing_finished.emit()
            self._cleanup()

    @pyqtSlot(int, str)
    def _on_worker_status_update(self, row_index: int, status: str):
        """Handles status updates from the worker and emits the final result."""
        if status in ("Success", "Failed", "Stopped"):
            if status == "Success":
                log_message = styled_text('bold', 'green', None, "Join process completed successfully.")
            else:
                log_message = styled_text('bold', 'red', None, f"Failed to join videos. Status: {status}")
            self.log_signal.emit(log_message)
            self.processing_finished.emit()

    def _on_worker_thread_finished(self):
        """Cleans up resources after the worker thread has completely finished."""
        self._cleanup()

    def _cleanup(self):
        """Removes temporary files and resets worker state."""
        if self._temp_concat_file_path and os.path.exists(self._temp_concat_file_path):
            try:
                os.remove(self._temp_concat_file_path)
                self.log_signal.emit(styled_text('bold', 'green', None, f"Cleaned up temporary file: {os.path.basename(self._temp_concat_file_path)}"))
            except OSError as e:
                self.log_signal.emit(styled_text('bold', 'red', None, f"Error removing temporary file: {e}"))
        
        self._worker = None
        self._temp_concat_file_path = None
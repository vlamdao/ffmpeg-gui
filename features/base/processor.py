import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from abc import ABC, abstractmethod
from processor import FFmpegWorker
from helper import styled_text


class BaseProcessor(QObject):
    """
    Abstract base class for feature processors that interact with FFmpeg.
    Provides common functionality for starting, stopping, and managing FFmpegWorker.
    """
    log_signal = pyqtSignal(str)
    processing_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: FFmpegWorker | None = None

    def is_running(self) -> bool:
        """Checks if a process is currently active."""
        return self._worker is not None and self._worker.isRunning()

    def stop(self):
        """Stops the running worker thread."""
        if self.is_running():
            self._worker.stop()
            self.log_signal.emit(styled_text('bold', 'blue', None, f"Features: {self.get_feature_name()} | "
                                                                    f"Process stopped"))
            self.processing_finished.emit()
            self._cleanup()
    
    @abstractmethod
    def get_feature_name(self) -> str:
        """Returns the name of the feature being processed."""
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def _prepare_job(self, *args, **kwargs) -> tuple[list[tuple[str, list[str]], str]]:
        """Return a tuple (jobs, message)
            jobs = [(job_id, [command])]
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def start(self, *args, **kwargs):
        if self.is_running():
            msg = (f"Features: {self.get_feature_name()} | " 
                   f"Process is already in progress.")
            self.log_signal.emit(styled_text('bold', 'blue', None, msg))
            return

        try:
            prepaird_job = self._prepare_job(*args, **kwargs)

            jobs, message = prepaird_job
            if not jobs:
                self.processing_finished.emit()
                self.log_signal.emit(styled_text('bold', 'red', None, message))
                return
            self._start_worker(jobs=jobs)
            self.log_signal.emit(styled_text('bold', 'blue', None, message))
        except Exception as e:
            self.log_signal.emit(styled_text('bold', 'red', None, f'Features: {self.get_feature_name()} | '
                                                                    f'Error: {e}'))
            self.processing_finished.emit()
            self._cleanup()

    def _start_worker(self, jobs: list[tuple[str, list[str]]]):
        """Initializes and starts the FFmpegWorker."""
        self._worker = FFmpegWorker(jobs=jobs)
        self._worker.log_signal.connect(self.log_signal)
        self._worker.status_updated.connect(self._on_worker_status_update)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.start()

    @pyqtSlot(str, str)
    def _on_worker_status_update(self, job_id: str, status: str):
        """Handles status updates from the worker and emits the final result."""
        if status in ("Success", "Failed", "Stopped"):
            if status == "Success":
                log_message = styled_text('bold', 'green', None, f"Features: {self.get_feature_name()} | "
                                                                    f"Process completed successfully.")
            else:
                log_message = styled_text('bold', 'red', None, f"Features: {self.get_feature_name()} | "
                                                                    f"Process failed. Status: {status}")
            self.log_signal.emit(log_message)
            self.processing_finished.emit()

    def _on_worker_thread_finished(self):
        """Cleans up resources after the worker thread has completely finished."""
        self._cleanup()

    def _cleanup(self):
        """Resets worker state and performs any necessary cleanup."""
        self._worker = None

from PyQt5.QtCore import QObject, pyqtSignal

from processor import FFmpegWorker

class SegmentProcessor(QObject):
    """
    Manages the sequential processing of video segments.

    This class encapsulates the logic for queuing segments, running FFmpeg workers
    one by one, and updating the UI to reflect the current state. It is designed
    to be controlled by a parent controller (like VideoCutter).
    """

    # Signals to report progress to the UI layer
    processing_started = pyqtSignal(int) # Emits the total number of segments to be processed
    processing_stopped = pyqtSignal()    # Emitted when processing stops for any reason
    segment_processing = pyqtSignal(tuple) # Emits the (start, end) tuple of the segment
    segment_processed = pyqtSignal(tuple) # Emits the (start, end) tuple of a completed segment

    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self._logger = logger

        self._active_workers = []
        self._processing_queue = []

    def start_processing(self, segments_to_process: list[tuple[int, int]]):
        """Initiates the sequential cutting process for all defined segments."""
        if self._processing_queue or self._active_workers:
            self._logger.append_log("WARNING: A cutting process is already running.")
            return

        # Populate the processing queue
        self._processing_queue = list(segments_to_process)
        
        self.processing_started.emit(len(self._processing_queue))

        self._logger.append_log(f"INFO: Starting to cut {len(self._processing_queue)} segments sequentially.")
        self._process_next_in_queue()

    def stop_processing(self):
        """Stops the current cutting process."""
        if not self._processing_queue and not self._active_workers:
            self._logger.append_log("INFO: No cutting process is currently running.")
            return

        self._logger.append_log("INFO: Stopping all cutting processes...")
        self._processing_queue.clear()
        for worker in self._active_workers:
            worker.stop()
        self._active_workers.clear()
        self.processing_stopped.emit()

    def _process_next_in_queue(self):
        """Processes the next segment in the queue."""
        if not self._processing_queue:
            self._logger.append_log("INFO: All segments have been processed.")
            self.processing_stopped.emit()
            return

        # Get the data for the next segment from the queue
        segment_data, command = self._processing_queue.pop(0)
        self.segment_processing.emit(segment_data)

        self._start_cut_worker(segment_data, command)

    def _on_worker_finished(self, worker_ref, segment_data):
        """Handles cleanup and triggers the next item in the queue."""
        was_stopped = worker_ref not in self._active_workers

        if not was_stopped:
            self._active_workers.remove(worker_ref)
            self.segment_processed.emit(segment_data)
            self._process_next_in_queue()

    def _start_cut_worker(self, segment_data: tuple[int, int], command: str):
        """Creates and starts an FFmpegWorker for a single segment."""
        worker = FFmpegWorker(
            selected_files=[],
            command_input=None,
            output_path=None,
            command_override=command
        )
        worker.log_signal.connect(self._logger.append_log)
        worker.finished.connect(
            lambda w=worker, data=segment_data: self._on_worker_finished(w, data)
        )
        self._active_workers.append(worker)
        worker.start()

    def get_active_workers(self):
        """Returns the list of active workers."""
        return self._active_workers

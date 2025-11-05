import ast
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from processor.ffmpeg_worker import FFmpegWorker
from helper import styled_text

class Processor(QObject):
    """
    Manages the sequential processing of video segments.

    This class encapsulates the logic for queuing segments, running FFmpeg workers
    one by one, and updating the UI to reflect the current state. It is designed
    to be controlled by a parent controller (like VideoCutter).
    """

    # Signals to report progress to the UI layer
    processing_started = pyqtSignal(int) # Emits the total number of segments to be processed
    processing_stopped = pyqtSignal()    # Emitted when processing stops for any reason
    status_updated = pyqtSignal(tuple, str) # Emits (segment_data, status)
    segment_processed = pyqtSignal(tuple) # Emits the (start, end) tuple of a completed segment
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_workers = []
        self._processing_queue = []

    def start(self, jobs: list[tuple[str, list[str]]]):
        """Initiates the sequential cutting process for all defined segments."""
        if self._processing_queue or self._active_workers:
            self.log_signal.emit(styled_text('bold', 'blue', None, f"Features: Video Cutter | "
                                                                    f"WARNING: A cutting process is already running."))
            return

        # Set processing queue
        self._processing_queue = jobs
        self.processing_started.emit(len(self._processing_queue))
        self._process_next_in_queue()

    def _process_next_in_queue(self):
        """Processes the next segment in the queue."""
        if not self._processing_queue:
            self.log_signal.emit(styled_text('bold', 'blue', None, f"Features: Video Cutter | "
                                                                    f"All segments have been processed."))
            self.processing_stopped.emit()
            return

        # Get the data for the next segment from the queue
        job = self._processing_queue.pop(0)
        self._start_worker(job)
        
    def _start_worker(self, job):
        """Creates and starts an FFmpegWorker for a single segment."""
        # FFmpeg can process list of job,
        # but in here we used queue, so worker only process 1 job each time
        job_id, commands, outputfile_path = job

        worker = FFmpegWorker([(job_id, commands)])
        worker.set_outputfile_path(outputfile_path)
        worker.log_signal.connect(self.log_signal)
        worker.status_updated.connect(self._on_worker_status_update)
        worker.finished.connect(
            lambda w=worker, j_id=job_id: self._on_worker_finished(w, j_id)
        )
        self._active_workers.append(worker)
        worker.start()

    def _on_worker_finished(self, worker_ref, job_id: str):
        """Handles cleanup and triggers the next item in the queue."""
        was_stopped = worker_ref not in self._active_workers

        if not was_stopped:
            self._active_workers.remove(worker_ref)
            try:
                segment_data = ast.literal_eval(job_id)
                self.segment_processed.emit(segment_data)
            except Exception as e:
                self.log_signal.emit(styled_text('bold', 'red', None, f"Features: Video Cutter | "
                                                                        f"Exception: {e}"))
            self._process_next_in_queue()

    @pyqtSlot(str, str)
    def _on_worker_status_update(self, job_id: str, status: str):
        """Receives status from worker and forwards it to the main dialog."""
        try:
            segment_data = ast.literal_eval(job_id)
            self.status_updated.emit(segment_data, status)
        except Exception as e:
            self.log_signal.emit(styled_text('bold', 'red', None, f"Features: Video Cutter | "
                                                                    f"Exception: {e}"))

    def stop(self):
        """Stops the current cutting process."""
        if not self._processing_queue and not self._active_workers:
            self.log_signal.emit(styled_text('bold', 'blue', None, "Features: Video Cutter | "
                                                                    f"No cutting process is currently running."))
            return

        # Emit "Stopped" status for all segments remaining in the queue
        for job in self._processing_queue:
            try: # job is (job_id, commands, output_filepath)
                segment_data = ast.literal_eval(job[0]) 
                self.status_updated.emit(segment_data, "Stopped")
            except Exception as e:
                self.log_signal.emit(styled_text('bold', 'red', None, f"Features: Video Cutter | "
                                                                        f"Exception: {e}"))
            
        self._processing_queue.clear()
        for worker in self._active_workers:
            worker.stop()
        # self._active_workers.clear() # Let the wait() method handle the cleanup
        self.processing_stopped.emit()
    
    def wait(self):
        """Waits for all active worker threads to finish."""
        for worker in self._active_workers:
            if worker.isRunning():
                worker.wait()

    def get_active_workers(self):
        """Returns the list of active workers."""
        return self._active_workers

    def get_processing_queue(self):
        """Returns the list of jobs in the processing queue."""
        return self._processing_queue
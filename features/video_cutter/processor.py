import os
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor

from processor import FFmpegWorker
from helper import ms_to_time_str

from .components import SegmentManager, SegmentList, CommandTemplate
from .components.command.command import CommandContext

class SegmentProcessor(QObject):
    """
    Manages the sequential processing of video segments.

    This class encapsulates the logic for queuing segments, running FFmpeg workers
    one by one, and updating the UI to reflect the current state. It is designed
    to be controlled by a parent controller (like VideoCutter).
    """

    def __init__(self, video_path: str, output_path: str, segment_manager: SegmentManager,
                 segment_list: SegmentList, command_template: CommandTemplate, logger, parent=None):
        super().__init__(parent)
        self._video_path = video_path
        self._output_path = output_path
        self._segment_manager = segment_manager
        self._segment_list = segment_list
        self._command_template = command_template
        self._logger = logger

        self._active_workers = []
        self._processing_queue = []

    def start_processing(self):
        """Initiates the sequential cutting process for all defined segments."""
        if self._processing_queue or self._active_workers:
            self._logger.append_log("WARNING: A cutting process is already running.")
            return

        segments_to_process = self._segment_manager.get_segments_for_processing()
        if not segments_to_process:
            return

        # Populate the processing queue
        self._processing_queue = list(segments_to_process)

        # Visually mark all segments in the list as "pending" (yellow)
        pending_color = QColor("#fff3cd")  # A light yellow color
        for i in range(len(self._processing_queue)):
            self._segment_list.highlight_row(i, pending_color, clear_others=False)

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
        self._segment_list.clear_highlight()

    def _process_next_in_queue(self):
        """Processes the next segment in the queue."""
        if not self._processing_queue:
            self._logger.append_log("INFO: All segments have been processed.")
            self._segment_list.clear_highlight()
            return

        # The segment to process is always the first one in the UI list
        current_row_in_ui = 0
        # Highlight the current segment as "processing" (green) without clearing other highlights
        self._segment_list.highlight_row(current_row_in_ui, clear_others=False)

        # Get the data for the next segment from the queue
        start_ms, end_ms = self._processing_queue.pop(0)

        self._start_cut_worker(start_ms, end_ms, current_row_in_ui)

    def _on_worker_finished(self, worker_ref, segment_row_index):
        """Handles cleanup and triggers the next item in the queue."""
        was_stopped = worker_ref not in self._active_workers

        if not was_stopped:
            self._active_workers.remove(worker_ref)
            self._segment_manager.delete_segment(segment_row_index)
            self._process_next_in_queue()

    def _start_cut_worker(self, start_ms, end_ms, segment_row_index):
        """Creates and starts an FFmpegWorker for a single segment."""
        command_template = self._command_template.get_command_template()
        if not command_template:
            self._logger.append_log("ERROR: Command template is empty. Please define a command template before cutting.")
            return
            
        start_str = ms_to_time_str(start_ms)
        end_str = ms_to_time_str(end_ms)

        safe_start_str = start_str.replace(":", "-").replace(".", "_")
        safe_end_str = end_str.replace(":", "-").replace(".", "_")

        inputfile_name, inputfile_ext = os.path.splitext(os.path.basename(self._video_path))

        context = CommandContext(
            inputfile_folder=os.path.dirname(self._video_path),
            inputfile_name=inputfile_name,
            inputfile_ext=inputfile_ext.lstrip('.'),
            start_time=start_str,
            end_time=end_str,
            output_folder=self._output_path,
            safe_start_time=safe_start_str,
            safe_end_time=safe_end_str
        )
        command = self._command_template.generate_command(context)

        worker = FFmpegWorker(
            selected_files=[],
            command_input=None,
            output_path=None,
            command_override=command
        )
        worker.log_signal.connect(self._logger.append_log)
        worker.finished.connect(
            lambda w=worker, idx=segment_row_index: self._on_worker_finished(w, idx)
        )
        self._active_workers.append(worker)
        worker.start()

    def get_active_workers(self):
        """Returns the list of active workers."""
        return self._active_workers

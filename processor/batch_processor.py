import os
from PyQt5.QtCore import QObject, pyqtSignal
from processor import FFmpegWorker
from components import FileManager, CommandInput, OutputFolder
from .command_generator import CommandGenerator
from helper import styled_text

class BatchProcessor(QObject):
    """
    Orchestrates the batch processing of files using FFmpeg.

    This class acts as a controller that takes the user's selections (files,
    command, output path) and manages the lifecycle of an FFmpegWorker thread
    to execute the tasks in the background. It handles UI updates related to
    the processing state, such as clearing logs and updating file statuses.
    """
    log_signal = pyqtSignal(str)
    processing_finished = pyqtSignal()
    processing_started = pyqtSignal()

    def __init__(self,
                 file_manager: FileManager,
                 command_input: CommandInput,
                 output_folder: OutputFolder,
                 parent=None):

        super().__init__(parent)
        self._active_workers: list[FFmpegWorker] = []
        self._job_queue: list[tuple] = []
        self._file_manager = file_manager
        self._command_input = command_input
        self._output_folder = output_folder

    def run_command(self, selected_files: list[tuple[int, str, str]]):
        """Starts the batch processing of selected files."""
        if self.is_processing():
            self.log_signal.emit(styled_text('bold', 'blue', None, "A batch process is already running."))
            return

        self._job_queue = self._create_jobs(selected_files)
        if not self._job_queue:
            self.log_signal.emit(styled_text('bold', 'red', None, "Could not generate any commands to run."))
            return
        
        # Update status to "Pending" for all files in the queue
        for job_id, _, _ in self._job_queue:
            self._file_manager.update_status_by_filepath(job_id, "Pending")

        self.processing_started.emit()
        self.log_signal.emit(styled_text('bold', 'blue', None, f"Starting batch processing for {len(self._job_queue)} files..."))
        self._process_next_in_queue()

    def _create_jobs(self, selected_files: list) -> list[tuple[str, list[str], str]]:
        """Creates a list of FFmpeg commands to be executed."""
        jobs = []
        cmd_generator = CommandGenerator()
        command_template = self._command_input.get_command()
        # Standard command for each file
        for _, filename, folder in selected_files:
            file_path = os.path.join(folder, filename)
            output_folder_path = self._output_folder.get_completed_output_folder(folder)
            os.makedirs(output_folder_path, exist_ok=True)
            command = cmd_generator.generate_command(input_file=file_path,
                                                     output_folder=self._output_folder.get_completed_output_folder(folder),
                                                     command_template=command_template
                                                     )
            if command:
                # The output file path is the last quoted string in the command
                output_filepath = command.split('"')[-2]
                jobs.append((file_path, [command], output_filepath))
        return jobs

    def _process_next_in_queue(self):
        """Processes the next job in the queue."""
        if not self._job_queue:
            self.log_signal.emit(styled_text('bold', 'green', None, "Batch processing finished."))
            self.processing_finished.emit()
            return

        job = self._job_queue.pop(0)
        self._start_worker(job)

    def _start_worker(self, job: tuple[str, list[str], str]):
        """Initializes and starts an FFmpegWorker for a single job."""
        job_id, commands, output_filepath = job

        worker = FFmpegWorker([(job_id, commands)])
        worker.set_outputfile_path(output_filepath)
        worker.status_updated.connect(self._file_manager.update_status_by_filepath)
        worker.log_signal.connect(self.log_signal.emit)
        worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
        
        self._active_workers.append(worker)
        worker.start()

    def stop_batch(self):
        """Stops the currently running batch process."""
        if self.is_processing():
            # Mark remaining jobs in queue as stopped
            for job_id, _, _ in self._job_queue:
                self._file_manager.update_status_by_filepath(job_id, "Stopped")
            self._job_queue.clear()

            # Stop all currently active workers
            for worker in self._active_workers:
                worker.stop()
            
            # The _on_worker_finished will handle cleanup and emit processing_finished
            self.log_signal.emit(styled_text('bold', 'blue', None, "Stopped batch processing..."))

    def is_processing(self):
        """
        Checks if a batch process is currently active.
        """
        return bool(self._job_queue or self._active_workers)
    
    def _on_worker_finished(self, worker: FFmpegWorker):
        """
        Slot called when the FFmpegWorker thread has finished.
        """
        if worker in self._active_workers:
            self._active_workers.remove(worker)

        # If the process was not stopped by the user, continue with the next job
        if not worker._is_stopped:
            self._process_next_in_queue()
        # If it was stopped, and it's the last active worker, then the whole batch is finished.
        elif not self._active_workers:
             self.processing_finished.emit()
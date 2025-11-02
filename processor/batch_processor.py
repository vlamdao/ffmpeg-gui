from PyQt5.QtCore import QObject, pyqtSignal
from processor import FFmpegWorker
from components import FileManager, CommandInput, OutputFolder
from .command_generator import CommandGenerator
from helper import bold_blue, bold_red, bold_green, bold_yellow

class BatchProcessor(QObject):
    """
    Orchestrates the batch processing of files using FFmpeg.

    This class acts as a controller that takes the user's selections (files,
    command, output path) and manages the lifecycle of an FFmpegWorker thread
    to execute the tasks in the background. It handles UI updates related to
    the processing state, such as clearing logs and updating file statuses.
    """
    log_signal = pyqtSignal(str)

    def __init__(self,
                 file_manager: FileManager,
                 command_input: CommandInput,
                 output_folder: OutputFolder,
                 parent=None):
        """Initializes the BatchProcessor.

        Args:
            file_manager (FileManager): The file manager component.
            command_input (CommandInput): The command input component.
            output_folder (OutputFolder): The output folder component.
            logger (Logger): The logger component.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self._ffmpeg_worker = None
        self._file_manager = file_manager
        self._command_input = command_input
        self._output_folder = output_folder

    def _create_jobs(self, selected_files: list) -> list[tuple[int, list[str]]]:
        """Creates a list of FFmpeg commands to be executed."""
        cmd_generator = CommandGenerator(selected_files, self._command_input, self._output_folder)
        jobs = []

        # Standard command for each file
        for row_index, filename, folder in selected_files:
            current_file_tuple = (row_index, filename, folder)
            command = cmd_generator.generate_command(current_file_tuple)
            if command:
                jobs.append((row_index, [command]))
        return jobs

    def _start_batch(self, jobs: list[tuple[int, list[str]]], selected_rows: set):
        """
        Initializes and starts the FFmpegWorker for the batch job.

        Args:
            jobs (list): A list of tuples (row_index, command_string).
            selected_rows (set): A set of row indices for the selected files.
        """
        # Update status to "Pending" for all selected files in the jobs
        for row in selected_rows:
            self._file_manager.update_status(row, "Pending")

        # Clear status for any previously selected but now unselected files
        for row in range(self._file_manager.file_table.rowCount()):
            if row not in selected_rows:
                self._file_manager.update_status(row, "")

        # Create and start worker
        self._ffmpeg_worker = FFmpegWorker(jobs)
        self._ffmpeg_worker.update_status.connect(self._file_manager.update_status)
        self._ffmpeg_worker.log_signal.connect(self.log_signal.emit)
        self._ffmpeg_worker.finished.connect(self._on_worker_finished)
        self._ffmpeg_worker.start()
    
    def _on_worker_finished(self):
        """
        Slot called when the FFmpegWorker thread has finished.

        Cleans up the worker reference to indicate that no process is running.
        """
        self._ffmpeg_worker = None
    
    def stop_batch(self):
        """Stops the currently running batch process."""
        if self.is_processing():
            self._ffmpeg_worker.stop()
            self.log_signal.emit(bold_blue("Stopped batch processing..."))

    def run_command(self, selected_files: list[tuple[int, str, str]]):
        """Starts the batch processing of selected files."""
        if self.is_processing():
            self.log_signal.emit(bold_yellow("A batch process is already running."))
            return

        selected_rows = set(row for row, _, _ in selected_files)
        
        jobs = self._create_jobs(selected_files)
        if not jobs:
            self.log_signal.emit(bold_red("Could not generate any commands to run."))
            return
        self._start_batch(jobs, selected_rows)

    def is_processing(self):
        """
        Checks if a batch process is currently active.

        Returns:
            bool: True if a worker is running, False otherwise.
        """
        return self._ffmpeg_worker is not None and self._ffmpeg_worker.isRunning()
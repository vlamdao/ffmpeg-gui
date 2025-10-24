from PyQt5.QtCore import QObject, pyqtSignal
from processor import FFmpegWorker
from components import FileManager, CommandInput, OutputPath, Logger

class BatchProcessor(QObject):
    """
    Orchestrates the batch processing of files using FFmpeg.

    This class acts as a controller that takes the user's selections (files,
    command, output path) and manages the lifecycle of an FFmpegWorker thread
    to execute the tasks in the background. It handles UI updates related to
    the processing state, such as clearing logs and updating file statuses.
    """
    log_signal = pyqtSignal(str)

    def __init__(self, parent):
        """Initializes the BatchProcessor.

        Args:
            parent (QWidget): The main application window which holds references to other components.
        """
        super().__init__(parent)
        self.parent = parent
        self._ffmpeg_worker = None

        # Store references to components from the main app
        self._file_manager: FileManager = self.parent.file_manager
        self._command_input: CommandInput = self.parent.command_input
        self._output_path: OutputPath = self.parent.output_path
        self._logger: Logger = self.parent.logger

    def _start_batch(self, selected_files: list, selected_rows: set):
        """
        Initializes and starts the FFmpegWorker for the batch job.

        This method updates the status of selected files to "Pending", clears the
        status for unselected files, creates a new FFmpegWorker instance, connects
        its signals, and starts the background thread.

        Args:
            selected_files (list): A list of tuples containing file information.
            selected_rows (set): A set of row indices for the selected files.
        """
        # Update status to "Pending" for selected files
        for row in selected_rows:
            self._file_manager.update_status(row, "Pending")

        # Clear status for unselected files
        for row in range(self._file_manager.file_table.rowCount()):
            if row not in selected_rows:
                self._file_manager.update_status(row, "")

        # Create and start worker
        self._ffmpeg_worker = FFmpegWorker(selected_files, self._command_input, self._output_path)
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
            self.log_signal.emit("Stopped batch processing...")

    def run_command(self):
        """Starts the batch processing of selected files."""
        if self.is_processing():
            self.log_signal.emit("A batch process is already running.")
            return
        self._logger.clear()

        selected_files, selected_rows = self._file_manager.get_selected_files()
        if not selected_files:
            self.log_signal.emit("No items selected to process.")
            return
        
        self._start_batch(selected_files, selected_rows)

    def add_to_queue_and_run(self, command, output_file):
        """
        Adds a single, pre-defined command to the processing queue and runs it.

        This is designed for features like the Video Cutter that generate their
        own FFmpeg commands. It will not run if another process is already active.

        Args:
            command (str): The full FFmpeg command to execute.
            output_file (str): The path to the expected output file.
        """
        if self.is_processing():
            self.log_signal.emit("Another process is already running. Please wait.")
            return

        self._logger.clear()
        self.log_signal.emit("Starting single command processing...")

        # We pass an empty list for selected_files as it's not used for command_override
        self._ffmpeg_worker = FFmpegWorker(
            selected_files=[],
            command_input=self._command_input, # Still needed for constructor
            output_path=self._output_path,     # Still needed for constructor
            command_override=command
        )
        self._ffmpeg_worker.log_signal.connect(self.log_signal.emit)
        self._ffmpeg_worker.finished.connect(self._on_worker_finished)
        self._ffmpeg_worker.start()
    def is_processing(self):
        """
        Checks if a batch process is currently active.

        Returns:
            bool: True if a worker is running, False otherwise.
        """
        return self._ffmpeg_worker is not None and self._ffmpeg_worker.isRunning()
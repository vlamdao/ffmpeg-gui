from PyQt5.QtCore import QObject, pyqtSignal
from processor import FFmpegWorker
from components import FileManager, CommandInput, OutputPath, Logger

class BatchProcessor(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._ffmpeg_worker = None

        # Store references to components from the main app
        self._file_manager: FileManager = self.parent.file_manager
        self._command_input: CommandInput = self.parent.command_input
        self._output_path: OutputPath = self.parent.output_path
        self._logger: Logger = self.parent.logger

    def _start_batch(self, selected_files: list, selected_rows: set):
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
        self._ffmpeg_worker = None
    
    def stop_batch(self):
        if self.is_processing():
            self._ffmpeg_worker.stop()
            self.log_signal.emit("Stopped batch processing...")

    def run_command(self):
        if self.is_processing():
            self.log_signal.emit("A batch process is already running.")
            return
        self._logger.clear()

        selected_files, selected_rows = self._file_manager.get_selected_files()
        if not selected_files:
            self.log_signal.emit("No items selected to process.")
            return
        
        self._start_batch(selected_files, selected_rows)

    def is_processing(self):
        return self._ffmpeg_worker is not None and self._ffmpeg_worker.isRunning()
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QLabel
from processor import FFmpegWorker
from components import FileManager, CommandInput, OutputPath, Logger

class BatchProcessor(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.selected_files = []        # Selected files for processing
        self.selected_rows = set()      # Selected rows for update status

    def run_command(self, 
                    file_manager: FileManager, 
                    command_input: CommandInput, 
                    output_path: OutputPath, 
                    logger: Logger):
        
        logger.clear()
        
        # Get selected files and rows
        # selected_files: List[str], selected_rows: Set[int]
        # selected_files for processing, selected_rows for status update
        self.selected_files, self.selected_rows = file_manager.get_selected_files()
        
        if not self.selected_files:
            self.log_signal.emit("No items selected to process.")
            return
        
        self.start_batch(file_manager, command_input, output_path)

    def start_batch(self, 
                    file_manager: FileManager, 
                    command_input: CommandInput, 
                    output_path: OutputPath):
        
        # Update status to "Pending" for selected files
        for row in self.selected_rows:
            file_manager.update_status(row, "Pending")
        
        # Clear status for unselected files
        for row in range(file_manager.file_table.rowCount()):
            if row not in self.selected_rows:
                file_manager.update_status(row, "")

        # Create and start worker
        self.worker = FFmpegWorker(self.selected_files, command_input, output_path)
        self.worker.update_status.connect(file_manager.update_status)
        self.worker.log_signal.connect(self.log_signal.emit)
        self.worker.start()

    def stop_batch(self, file_manager: FileManager):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_signal.emit("Stopped batch processing...")

        # Update status of selected files to "Stopped" if they were pending or processing
        # The status column is at index 7
        for row in self.selected_rows:
            status_widget = file_manager.file_table.cellWidget(row, 7)
            if status_widget and isinstance(status_widget, QLabel):
                current_status = status_widget.toolTip()
                if current_status in ["Pending", "Processing"]:
                    file_manager.update_status(row, "Stopped")

    def is_processing(self):
        return self.worker is not None and self.worker.isRunning()
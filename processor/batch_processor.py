from PyQt5.QtCore import QObject, pyqtSignal
from processor import FFmpegWorker

class BatchProcessor(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.selected_files = []        # Selected files for processing
        self.selected_rows = set()      # Selected rows for update status

    def run_command(self, file_manager, command_input, output_path, logger):
        """Start processing the selected files
            Args:
                file_manager (FileManager): The file manager instance
                command_input (CommandInput): The command input instance
                output_path (OutputPath): The output path instance
                logger (Logger): The logger instance
        """
        # Clear previous logs
        logger.clear()

        # Save selected files and rows after "Run" is clicked
        self.selected_files, self.selected_rows = file_manager.get_selected_files()
        if not self.selected_files:
            self.log_signal.emit("No items selected to process.")
            return
        
         # Start batch processing
        self.start_batch(file_manager, command_input, output_path)

    def start_batch(self, file_manager, command_input, output_path):
        """Start batch processing"""
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

    def stop_batch(self, file_manager):
        """Stop batch processing"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_signal.emit("Stopped batch processing...")

        # Update status of selected files to "Stopped" if they were pending or processing
        for row in self.selected_rows:
            widget = file_manager.file_table.cellWidget(row, 4)
            if widget is not None:
                if hasattr(widget, 'status') and widget.status in ["Pending", "Processing"]:
                    file_manager.update_status(row, "Stopped")
            else:
                status_item = file_manager.file_table.item(row, 4)
                if status_item is not None and status_item.text() in ["Pending", "Processing"]:
                    file_manager.update_status(row, "Stopped")

    def is_processing(self):
        """Check if batch processing is running"""
        return self.worker is not None and self.worker.isRunning()
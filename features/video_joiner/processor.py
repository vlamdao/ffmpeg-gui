import os
import tempfile
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from processor import FFmpegWorker

class VideoJoinerProcessor(QObject):
    """
    Handles the background processing for joining videos using FFmpeg.
    """
    log_signal = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str)  # success (bool), status_message (str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: FFmpegWorker | None = None
        self._temp_concat_file_path: str | None = None

    def is_running(self) -> bool:
        """Checks if a join process is currently active."""
        return self._worker is not None and self._worker.isRunning()

    def start(self, selected_files: list[tuple[int, str, str]], output_path: str, command_template: str, join_method: str):
        """Starts the process of joining videos."""
        if self.is_running():
            self.log_signal.emit("Video joining is already in progress.")
            return

        try:
            command = self._create_command(selected_files, output_path, command_template, join_method)
            self._start_worker(command)
            self.log_signal.emit(f"Starting to join {len(selected_files)} files...")
        except Exception as e:
            error_msg = f"Could not start join process: {e}"
            self.log_signal.emit(f"Error preparing join job: {e}")
            self.processing_finished.emit(False, error_msg)
            self._cleanup()

    def _create_command(self, selected_files: list[tuple[int, str, str]], output_path: str, command_template: str, join_method: str) -> str:
        """Creates the final FFmpeg command string."""
        replacements = {"output_folder": output_path}

        if join_method == "demuxer":
            # Create a temporary file listing all videos to be concatenated
            concat_fd, concat_path = tempfile.mkstemp(suffix=".txt", text=True)
            with os.fdopen(concat_fd, 'w', encoding='utf-8') as f:
                for _, filename, folder in selected_files:
                    full_path = os.path.join(folder, filename).replace('\\', '/')
                    f.write(f"file '{full_path}'\n")
            self._temp_concat_file_path = concat_path
            replacements["concatfile_path"] = concat_path

        elif join_method == "filter":
            inputs = " ".join([f'-i "{os.path.join(folder, filename)}"' for _, filename, folder in selected_files])
            filter_script = "".join([f"[{i}:v:0][{i}:a:0]" for i in range(len(selected_files))])
            filter_script += f"concat=n={len(selected_files)}:v=1:a=1[v][a]"
            replacements["inputs"] = inputs
            replacements["filter_script"] = filter_script

        # Replace placeholders in the user-provided command template
        for placeholder, value in replacements.items():
            command_template = command_template.replace(f"{{{placeholder}}}", value)

        return command_template

    def _start_worker(self, command: str):
        """Initializes and starts the FFmpegWorker."""
        job = (-1, [command])  # Use -1 for row_index as this is a single job
        self._worker = FFmpegWorker([job])
        self._worker.log_signal.connect(self.log_signal)
        self._worker.update_status.connect(self._on_worker_status_update)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.start()

    def stop(self):
        """Stops the running worker thread."""
        if self.is_running():
            self._worker.stop_all()
            self.log_signal.emit("Join process stopped by user.")

    @pyqtSlot(int, str)
    def _on_worker_status_update(self, row_index: int, status: str):
        """Handles status updates from the worker and emits the final result."""
        if status in ("Success", "Failed", "Stopped"):
            is_success = (status == "Success")
            if is_success:
                message = "Videos have been joined successfully."
            else:
                message = f"Failed to join videos. Status: {status}"
            self.processing_finished.emit(is_success, message)

    def _on_worker_thread_finished(self):
        """Cleans up resources after the worker thread has completely finished."""
        self._cleanup()

    def _cleanup(self):
        """Removes temporary files and resets worker state."""
        if self._temp_concat_file_path and os.path.exists(self._temp_concat_file_path):
            try:
                os.remove(self._temp_concat_file_path)
                self.log_signal.emit(f"Cleaned up temporary file: {os.path.basename(self._temp_concat_file_path)}")
            except OSError as e:
                self.log_signal.emit(f"Error removing temporary file: {e}")
        
        self._worker = None
        self._temp_concat_file_path = None
import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

from .command_generator import CommandGenerator

class FFmpegWorker(QThread):
    """
    A QThread worker for executing FFmpeg commands in the background to avoid
    blocking the main GUI thread.

    Signals:
        update_status (pyqtSignal): Emits (row_index, status_string) to update
                                    the status of a file in the UI.
        log_signal (pyqtSignal): Emits log messages to be displayed.
    """
    from components import CommandInput, OutputPath

    update_status = pyqtSignal(int, str)
    log_signal = pyqtSignal(str)

    def __init__(self,
                 selected_files: list[tuple[int, str, str]],
                 command_input: CommandInput,
                 output_path: OutputPath,
                 parent=None):
        super().__init__(parent)
        self._selected_files = selected_files
        self._command_input = command_input
        self._output_path = output_path
        self._proc = None
        self._is_stopped = False
        self._cmd_generator = CommandGenerator(self._selected_files, self._command_input, self._output_path)

    def _get_command_type(self) -> str:
        """Determines the command type based on the command template."""
        cmd_template = self._command_input.get_command()
        if "-f concat" in cmd_template:
            return "concat_demuxer"
        return "others_command"

    def run(self):
        """
        The main execution method of the thread.
        Generates and processes FFmpeg commands based on the command type.
        """
        self._is_stopped = False
        command_type = self._get_command_type()

        if command_type == "concat_demuxer":
            cmd = self._cmd_generator.generate_concat_command()
            if not cmd:
                return
            self._update_all_status("Processing")
            final_status = self._process_command(cmd)
            self._update_all_status(final_status)

        elif command_type == "others_command":
            files_to_process = list(self._selected_files)
            while files_to_process:
                # Get the next file from the front of the list to process
                row_index, filename, folder = files_to_process.pop(0)

                if self._is_stopped:
                    # Mark this and all remaining files as "Stopped"
                    self.update_status.emit(row_index, "Stopped")
                    for rem_row, _, _ in files_to_process:
                        self.update_status.emit(rem_row, "Stopped")
                    break  # Exit the loop

                current_file_tuple = (row_index, filename, folder)
                cmd = self._cmd_generator.generate_others_command(current_file_tuple)
                if cmd:
                    self.update_status.emit(row_index, "Processing")
                    final_status = self._process_command(cmd)
                    self.update_status.emit(row_index, final_status)

    def _update_all_status(self, status: str):
        """Updates the status for all selected files."""
        for row_index, _, _ in self._selected_files:
            self.update_status.emit(row_index, status)

    def _process_command(self, cmd: str) -> str:
        """
        Executes a single FFmpeg command using subprocess.

        Args:
            cmd: The command string to execute.

        Returns:
            A status string: "Success", "Failed", or "Stopped".
        """
        self.log_signal.emit(f'<br><span style="color:blue; font-weight:bold">{cmd}</span>')
        try:
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'
            # Using shell=True can be a security risk if cmd contains unsanitized user input.
            # For this application, it's acceptable as we control the command generation.
            # A more robust solution would be to build a list of arguments.
            self._proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            for line in self._proc.stdout:
                if self._is_stopped:
                    self._proc.terminate()
                    try:
                        # Wait for 5 seconds for graceful termination
                        self._proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        self._proc.kill()
                    return "Stopped"
                self.log_signal.emit(line.rstrip())

            self._proc.wait()
            if self._is_stopped:
                return "Stopped"

            return "Success" if self._proc.returncode == 0 else "Failed"

        except Exception as e:
            self.log_signal.emit(f"Exception while running command: {e}")
            return "Failed"
        finally:
            self._proc = None

    def stop(self):
        """
        Sets the stop flag and attempts to terminate the running process.
        The running process loop will handle the cleanup.
        """
        self._is_stopped = True
        if self._proc and self._proc.poll() is None:
            # Terminate the process. The loop in process_command will handle it.
            self._proc.terminate()
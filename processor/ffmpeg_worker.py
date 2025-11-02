from __future__ import annotations
import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

class FFmpegWorker(QThread):
    """
    A QThread worker for executing FFmpeg commands in the background to avoid
    blocking the main GUI thread.

    Signals:
        update_status (pyqtSignal): Emits (row_index, status_string) to update
                                    the status of a file in the UI.
        log_signal (pyqtSignal): Emits log messages to be displayed.
    """
    update_status = pyqtSignal(int, str)
    log_signal = pyqtSignal(str)

    def __init__(self, jobs: list[tuple[int, list[str]]], parent=None):
        """Initializes the FFmpegWorker thread.

        Args:
            jobs (list[tuple[int, list[str]]]): A list of jobs to process. Each tuple
                contains (row_index, list_of_commands). A row_index of -1
                signifies a command that applies to all files (e.g., concat).
            parent (QObject, optional): The parent object. Defaults to None.
        """

        super().__init__(parent)
        self._jobs = jobs
        self._proc = None
        self._is_stopped = False

    def _process_command(self, cmd: str) -> str:
        """
        Executes a single FFmpeg command, captures its output, and handles termination.

        This method runs the command in a subprocess, reading stdout/stderr line by
        line and emitting it via the `log_signal`. It continuously checks the
        `_is_stopped` flag to allow for graceful termination of the process.

        Args:
            cmd (str): The complete FFmpeg command string to execute.

        Returns:
            str: A status string indicating the outcome: "Success", "Failed", or "Stopped".
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

    def run(self):
        """
        The main execution method of the thread.
        It iterates through the jobs it was given and executes the FFmpeg commands.
        """
        self._is_stopped = False

        jobs_to_process = list(self._jobs)

        while jobs_to_process:
            row_index, commands = jobs_to_process.pop(0)

            if self._is_stopped:
                # Mark this and all remaining files as "Stopped"
                if row_index != -1:
                    self.update_status.emit(row_index, "Stopped")
                for rem_row, _ in jobs_to_process:
                    if rem_row != -1:
                        self.update_status.emit(rem_row, "Stopped")
                break  # Exit the loop

            self.update_status.emit(row_index, "Processing")
            
            final_status = "Success"
            for i, cmd in enumerate(commands):
                status = self._process_command(cmd)
                if status != "Success":
                    final_status = status
                    break  # Stop processing commands for this job if one fails or is stopped

            self.update_status.emit(row_index, final_status)

    def stop(self):
        """
        Signals the worker to stop processing.

        This method sets a flag that is checked within the processing loops,
        and it attempts to terminate the current FFmpeg subprocess if one is running.
        """
        self._is_stopped = True
        if self._proc and self._proc.poll() is None:
            # Terminate the process. The loop in process_command will handle it.
            self._proc.terminate()
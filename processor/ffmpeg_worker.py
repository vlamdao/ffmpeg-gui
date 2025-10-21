import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from .command_generator import CommandGenerator

class FFmpegWorker(QThread):
    update_status = pyqtSignal(int, str)
    log_signal = pyqtSignal(str)

    def __init__(self, selected_files, command_input, output_path, parent=None):
        """Worker thread to process FFmpeg commands in batch
            Args:
                selected_files (list): List of tuples (row_index, filename, filepath)
                command_input (CommandInput): Command input instance
                output_path (OutputPath): Output path instance
                parent (QObject, optional): Parent QObject. Defaults to None.
        """
        super().__init__(parent)
        self.selected_files = selected_files
        self.command_input = command_input
        self.output_path = output_path
        self.proc = None
        self._is_stopped = False
        self.cmd_generator = CommandGenerator(self.selected_files, self.command_input, self.output_path)

    def get_command_type(self):
        cmd_template = self.command_input.get_command()
        if "-f concat" in cmd_template:
            return "concat_demuxer"
        return "others"

    def run(self):
        self._is_stopped = False
        command_type = self.get_command_type()
        
        match command_type:
            case "concat_demuxer":
                cmd = self.cmd_generator.generate_concat_command()
                if not cmd:
                    return
                # Update status of selected files to "Processing"
                self.update_all_status("Processing")
                
                success = self.process_command(cmd, self.selected_files[0][0])
                
                # Update status of all selected files after processing
                if success:
                    self.update_all_status("Successed")
                elif self._is_stopped:
                    self.update_all_status("Stopped")
                else:
                    self.update_all_status("Failed")

            case "others":
                for file in self.selected_files:
                    if self._is_stopped:
                        self.update_status.emit(file[0], "Stopped")
                        break
                    
                    cmd = self.cmd_generator.generate_others_command(file)
                    if cmd:
                        # Update status to "Processing" for current file
                        self.update_status.emit(file[0], "Processing")

                        success = self.process_command(cmd, file[0])

                        # Update status for processed file
                        if success:
                            self.update_status.emit(file[0], "Successed")
                        elif self._is_stopped:
                            self.update_status.emit(file[0], "Stopped")
                        else:
                            self.update_status.emit(file[0], "Failed")

            case _:
                # Default case: pass
                # because get_command_type return "others" by default
                pass

    def update_all_status(self, status):
        for file in self.selected_files:
            self.update_status.emit(file[0], status)
    
    def process_command(self, cmd, status_row):
        self.update_status.emit(status_row, "Processing")
        self.log_signal.emit(f"Command:\n{cmd}")

        try:
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'
            self.proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            # Read output line by line to:
            # - Emit log signals
            # - Check for stop flag and terminate if set and update status to "Stopped"
            for line in self.proc.stdout:
                if self._is_stopped:
                    self.proc.terminate()
                    self.update_status.emit(status_row, "Stopped")
                    return
                self.log_signal.emit(line.rstrip())
                
            self.proc.wait()
            if self._is_stopped:
                return
            
            # Determine success based on return code and emit status update
            success = (self.proc.returncode == 0)
            self.proc = None
            return success
            
        except Exception as e:
            self.log_signal.emit(f"Exception: {e}")
            self.proc = None
            return False

    def stop(self):
        self._is_stopped = True
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
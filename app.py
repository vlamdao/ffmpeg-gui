import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QShortcut, QApplication, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QIcon, QKeySequence
from helper import resource_path
from components import (PresetManager, Logger, FileManager, ControlPanel,
                        CommandInput, OutputFolder)

from features import VideoCutter, ThumbnailSetter, VideoJoiner
from processor import BatchProcessor

class FFmpegGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg GUI")
        self.resize(1400, 800)
        icon_path = resource_path("icon/ffmpeg.ico")
        self.setWindowIcon(QIcon(icon_path))

        self._setup_components()
        self._setup_layout()
        self._connect_signals()
        self._setup_shortcuts()

    def _setup_components(self):
        """Initialize all the core components of the application."""
        self.file_manager = FileManager(self)
        self.logger = Logger()
        self.command_input = CommandInput(self)
        self.output_folder = OutputFolder(self)
        self.preset_table = QTableWidget()
        self.preset_manager = PresetManager(self, self.preset_table, self.command_input.get_command_widget())
        self.batch_processor = BatchProcessor(
            file_manager=self.file_manager,
            command_input=self.command_input,
            output_folder=self.output_folder,
            parent=self)
        self.control_panel = ControlPanel(self) # Must be after other components

    def _setup_layout(self):
        """Set up the main window layout and add all component widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        top_layout = QHBoxLayout()

        # Top layout: File manager and Logger
        file_manager_widget = self.file_manager.get_widget()
        file_manager_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        top_layout.addWidget(file_manager_widget, 2)

        logger_widget = self.logger.get_widget()
        logger_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        # logger_widget.setFixedWidth(450)
        top_layout.addWidget(logger_widget, 1)
    
        main_layout.addLayout(top_layout)

        # Bottom components
        self.command_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.command_input)
        
        self.output_folder.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.output_folder)
        
        self.control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.control_panel)

        self.preset_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.preset_table)

    def _connect_signals(self):
        """Connect signals from components to the appropriate slots."""
        self.file_manager.log_signal.connect(self.logger.append_log)
        self.batch_processor.log_signal.connect(self.logger.append_log)
        self.preset_table.cellDoubleClicked.connect(self.preset_manager.apply_preset)
        self.preset_table.customContextMenuRequested.connect(self.preset_manager.show_context_menu)

        # Connect signals from ControlPanel to the appropriate slots/methods
        self.control_panel.add_files_clicked.connect(self.file_manager.add_files_dialog)
        self.control_panel.run_clicked.connect(self.run)
        self.control_panel.stop_clicked.connect(self.batch_processor.stop_batch)
        self.control_panel.remove_clicked.connect(self.file_manager.remove_selected_files)
        self.control_panel.cut_video_clicked.connect(self.open_video_cutter)
        self.control_panel.join_video_clicked.connect(self.open_video_joiner)
        self.control_panel.set_thumbnail_clicked.connect(self.open_thumbnail_setter)
        self.control_panel.add_preset_clicked.connect(self.preset_manager.add_preset)

    def _setup_shortcuts(self):
        """Set up global keyboard shortcuts."""
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close)

    def run(self):
        selected_files, _ = self.file_manager.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "Selection Error", "No files selected to process.")
            return
        if not self.command_input.get_command():
            QMessageBox.warning(self, "Command Error", "No command template entered.")
            return
        if not self.output_folder.get_folder():
            QMessageBox.warning(self, "Output Folder Error", "No output folder selected.")
            return
        self.batch_processor.run_command(selected_files)

    def open_video_cutter(self):
        selected_files, _ = self.file_manager.get_selected_files()
        if len(selected_files) != 1:
            QMessageBox.warning(self, "Selection Error", "Please select exactly one video file to cut.")
            return

        _, infile_name, infile_folder = selected_files[0]
        full_path = os.path.join(infile_folder, infile_name)
                
        output_folder = self.output_folder.get_completed_output_folder(infile_folder)
        logger = self.logger
        dialog = VideoCutter(
            input_file=full_path,
            output_folder=output_folder,
            logger=logger,
            parent=self)
        dialog.exec_()

    def open_thumbnail_setter(self):
        selected_files, _ = self.file_manager.get_selected_files()
        if len(selected_files) != 1:
            QMessageBox.warning(self, "Selection Error", 
                                    "Please select exactly one video file to set a thumbnail.")
            return

        _, infile_name, infile_folder = selected_files[0]
        full_path = os.path.join(infile_folder, infile_name)

        output_folder = self.output_folder.get_completed_output_folder(infile_folder)
        dialog = ThumbnailSetter(
            video_path=full_path,
            output_folder=output_folder,
            logger=self.logger,
            parent=self)
        dialog.exec_()

    def open_video_joiner(self):
        selected_files, _ = self.file_manager.get_selected_files()
        if len(selected_files) < 2:
            QMessageBox.warning(self, "Selection Error", 
                                    "Please select at least two video files to join.")
            return
        
        # Check if all selected files are in the same folder
        first_folder = selected_files[0][2]
        same_folder = all(folder == first_folder for _, _, folder in selected_files)

        if same_folder:
            output_folder = self.output_folder.get_completed_output_folder(first_folder)
        else:
            QMessageBox.warning(self, "Selection Error", 
                                    "Selected files must be in the same folder.")
            return
        
        dialog = VideoJoiner(
            selected_files=selected_files,
            output_folder=output_folder,
            logger=self.logger,
            parent=self
        )
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FFmpegGUI()
    window.show()
    sys.exit(app.exec_())
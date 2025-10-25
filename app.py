import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QShortcut, QApplication, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QIcon, QKeySequence
from helper import resource_path
from components import (PresetManager, Logger, FileManager, ControlPanel,
                        CommandInput, OutputPath)

from features.video_cutter import VideoCutter
from processor import BatchProcessor

class App(QMainWindow):
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
        self.output_path = OutputPath(self)
        self.preset_table = QTableWidget()
        self.preset_manager = PresetManager(self, self.preset_table, self.command_input.get_command_widget())
        self.batch_processor = BatchProcessor(self)
        self.control_panel = ControlPanel(self) # Must be after other components
        self.control_panel.enable_button('cut_video', False)

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
        logger_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        top_layout.addWidget(logger_widget, 1)

        main_layout.addLayout(top_layout)

        # Bottom components
        self.command_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.command_input)
        
        self.output_path.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.output_path)
        
        self.control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.control_panel)

        self.preset_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.preset_table)

    def _connect_signals(self):
        """Connect signals from components to the appropriate slots."""
        self.file_manager.log_signal.connect(self.logger.append_log)
        self.file_manager.get_widget().itemSelectionChanged.connect(self._update_control_buttons)
        self.batch_processor.log_signal.connect(self.logger.append_log)
        self.preset_table.cellDoubleClicked.connect(self.preset_manager.apply_preset)
        self.preset_table.customContextMenuRequested.connect(self.preset_manager.show_context_menu)

    def _setup_shortcuts(self):
        """Set up global keyboard shortcuts."""
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close)

    def _update_control_buttons(self):
        selected_files, _ = self.file_manager.get_selected_files()
        # Enable cut_video button only if exactly one file is selected
        self.control_panel.enable_button('cut_video', len(selected_files) == 1)

    def _setup_video_cutter(self):
        selected_files, _ = self.file_manager.get_selected_files()
        if len(selected_files) != 1:
            QMessageBox.warning(self, "Selection Error", "Please select exactly one video file to cut.")
            return

        _, inputfile_name, inputfile_path = selected_files[0]
        full_path = os.path.join(inputfile_path, inputfile_name)
        
        # Check if it's a video file (basic check)
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv']
        if not any(full_path.lower().endswith(ext) for ext in video_extensions):
            QMessageBox.warning(self, "Invalid File Type", "Please select a valid video file.")
            return
        
        output_path = self.output_path.get_completed_output_path(inputfile_path)
        logger = self.logger
        dialog = VideoCutter(
            video_path=full_path,
            output_path=output_path,
            logger=logger,
            parent=self)
        dialog.exec_()

    def open_video_cutter(self):
        self._setup_video_cutter()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
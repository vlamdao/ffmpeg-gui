import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QShortcut, QApplication, QSizePolicy)
from PyQt5.QtGui import QIcon, QKeySequence
from utils import resource_path
from components import (PresetManager, Logger, FileManager, ControlPanel, 
                        CommandInput, OutputPath)

from processor import BatchProcessor

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg GUI")
        self.resize(1300, 850)
        central = QWidget()
        self.setCentralWidget(central)
        icon_path = resource_path("icon/ffmpeg.ico")
        self.setWindowIcon(QIcon(icon_path))

        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # ============================================================
        # File manager setup
        # ============================================================
        self.file_manager = FileManager(self)
        self.file_manager.log_signal.connect(self.append_log)
        file_manager_widget = self.file_manager.get_widget()
        file_manager_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        top_layout.addWidget(file_manager_widget, 2)

        # ============================================================
        # Logger setup
        # ============================================================
        self.logger = Logger()
        logger_widget = self.logger.get_widget()
        logger_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        top_layout.addWidget(logger_widget, 1)

        # ============================================================
        # Command input setup
        # ============================================================
        self.command_input = CommandInput(self)
        self.command_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.command_input)
        
        # ============================================================
        # Output path setup
        # ============================================================
        self.output_path = OutputPath(self)
        self.output_path.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.output_path)
        
        # ============================================================
        # Controls setup
        # ============================================================
        self.control_panel = ControlPanel(self)
        self.control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(self.control_panel)

        # ============================================================
        # Preset table setup
        # ============================================================
        self.preset_table = QTableWidget()
        self.preset_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.preset_table)
        self.preset_manager = PresetManager(self, self.preset_table, self.command_input.get_command_widget())

        # ============================================================
        # Batch processor setup
        # ============================================================
        self.batch_processor = BatchProcessor(self)
        self.batch_processor.log_signal.connect(self.append_log)

    def append_log(self, msg):
        """Append message to logger"""
        self.logger.append_log(msg)

    def apply_preset_command(self, row: int):
        """Apply preset command when table row is double-clicked."""
        self.preset_manager.apply_preset(row)

    def preset_context_menu(self, pos):
        """Show context menu for preset table at the specified position."""
        self.preset_manager.show_context_menu(pos)

    def add_preset_dialog(self):
        """Show dialog to add a new FFmpeg command preset."""
        self.preset_manager.add_preset()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
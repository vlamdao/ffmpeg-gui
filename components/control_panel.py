from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from utils import resource_path

class ControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.button_style = """
            QPushButton {
                font-size: 13px;
                padding: 10px 20px;
                font-weight: semi-bold;
            }
        """
        self.buttons = {}
        self.setup_buttons()

    def setup_buttons(self):
        """Initialize all buttons with their properties"""
        button_configs = {
            'add_files': {
                'text': ' Add files',
                'icon': 'addfiles.png',
                'tooltip': 'Add files to the list',
                'connection': lambda: self.parent.file_manager.add_files_dialog()
            },
            'run': {
                'text': ' Run',
                'icon': 'run.png',
                'tooltip': 'Start processing files',
                'connection': self.parent.batch_processor.run_command
            },
            'stop': {
                'text': ' Stop',
                'icon': 'stop.png',
                'tooltip': 'Stop processing',
                'connection': self.parent.batch_processor.stop_batch
            },
            'remove': {
                'text': ' Remove',
                'icon': 'remove.png',
                'tooltip': 'Remove selected files',
                'connection': lambda: self.parent.file_manager.remove_selected_files()
            },
            'add_preset': {
                'text': ' Add preset',
                'icon': 'addpreset.png',
                'tooltip': 'Add new preset',
                'connection': self.parent.preset_manager.add_preset
            }
        }

        for btn_id, config in button_configs.items():
            self.add_button(btn_id, **config)

    def add_button(self, btn_id, text, icon, tooltip, connection):
        """Add a new button with specified properties"""
        button = QPushButton(text)
        button.setIcon(QIcon(resource_path(f"icon/{icon}")))
        button.setIconSize(QSize(24, 24))
        button.setStyleSheet(self.button_style)
        button.setMinimumHeight(40)
        button.setToolTip(tooltip)
        button.clicked.connect(connection)
        
        self.buttons[btn_id] = button
        self.layout.addWidget(button)

    def get_button(self, btn_id):
        """Get button by ID"""
        return self.buttons.get(btn_id)

    def add_custom_button(self, btn_id, text, icon, tooltip, connection):
        """Add a new custom button at runtime"""
        self.add_button(btn_id, text, icon, tooltip, connection)

    def remove_button(self, btn_id):
        """Remove a button by ID"""
        if btn_id in self.buttons:
            button = self.buttons.pop(btn_id)
            self.layout.removeWidget(button)
            button.deleteLater()

    def enable_button(self, btn_id, enabled=True):
        """Enable or disable a button"""
        if btn_id in self.buttons:
            self.buttons[btn_id].setEnabled(enabled)
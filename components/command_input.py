from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QTextEdit
)
from PyQt5.QtGui import QFont

class CommandInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Setup the command input interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setup_command_input(layout)

    def setup_command_input(self, parent_layout):
        """Setup the command input area"""
        cmd_layout = QHBoxLayout()
        
        cmd_label = QLabel("Command:")
        cmd_label.setFixedWidth(80)
        
        self.cmd_input = QTextEdit()
        self.cmd_input.setFixedHeight(50)
        self.cmd_input.setFont(QFont("Consolas", 9))
        
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_input)
        
        parent_layout.addLayout(cmd_layout)

    # Getter and Setter methods
    def get_command(self):
        """Get the current command text"""
        return self.cmd_input.toPlainText().strip()

    def set_command(self, text):
        """Set the command text"""
        self.cmd_input.setPlainText(text)

    def get_command_widget(self):
        """Get the command input widget
           Used by: PresetManager
        """
        return self.cmd_input

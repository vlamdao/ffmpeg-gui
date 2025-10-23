"""
Defines the CommandInput widget, a user interface component for entering FFmpeg commands.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QTextEdit
)
from PyQt5.QtGui import QFont

class CommandInput(QWidget):
    """A widget for inputting and managing an FFmpeg command template.

    This component provides a labeled, multi-line text input field where users
    can type or paste their FFmpeg command. It also includes methods to
    get and set the command text, and provides access to the underlying QTextEdit
    widget for integration with other components like the PresetManager.
    """
    def __init__(self, parent=None):
        """Initializes the CommandInput widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Sets up the user interface for the widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setup_command_input(layout)

    def setup_command_input(self, parent_layout):
        """Creates and configures the command input area.

        Args:
            parent_layout (QLayout): The parent layout to add the command input area to.
        """
        cmd_layout = QHBoxLayout()
        
        cmd_label = QLabel("Command:")
        cmd_label.setFixedWidth(80)
        
        self.cmd_input = QTextEdit()
        self.cmd_input.setFixedHeight(60)
        self.cmd_input.setFont(QFont("Consolas", 9))
        
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_input)
        
        parent_layout.addLayout(cmd_layout)

    def get_command(self) -> str:
        """Gets the current command text from the input field.

        Leading and trailing whitespace is stripped.

        Returns:
            str: The command template entered by the user.
        """
        return self.cmd_input.toPlainText().strip()

    def set_command(self, text: str):
        """Sets the text for the command input field.

        Useful for populating the command from a preset.

        Args:
            text (str): The text to set in the command input field.
        """
        self.cmd_input.setPlainText(text)

    def get_command_widget(self) -> QTextEdit:
        """Returns the QTextEdit widget instance.

        This method provides direct access to the input widget, allowing other
        components (like PresetManager) to interact with it, for example,
        to apply a preset.

        Returns:
            QTextEdit: The command input widget.
        """
        return self.cmd_input

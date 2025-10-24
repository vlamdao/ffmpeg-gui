from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from utils import resource_path

class ControlPanel(QWidget):
    """A widget that contains the main control buttons for the application.

    This panel groups buttons for core actions like adding files, running
    the conversion process, stopping it, removing files, and managing presets.
    It provides a centralized location for user interaction with the main
    functionalities of the application.
    """
    def __init__(self, parent=None):
        """Initializes the ControlPanel widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Sets up the user interface for the control panel."""
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
        """Initializes and configures all the standard control buttons.

        This method defines a dictionary of button configurations and uses it
        to create and add each button to the panel.
        """
        button_configs = {
            'add_files': {
                'text': ' Add files',
                'icon': 'addfiles.png',
                'tooltip': 'Add files to the list',
                'connection': lambda: self.parent.file_manager.add_files_dialog()
            },
            'cut_video': {
                'text': ' Cut Video',
                'icon': 'run.png',
                'tooltip': 'Cut a video into segments',
                'connection': lambda: self.parent.open_video_cutter()
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
        """Creates and adds a single button to the control panel.

        This is a factory method used by `setup_buttons` and `add_custom_button`.

        Args:
            btn_id (str): A unique identifier for the button.
            text (str): The text to display on the button.
            icon (str): The filename of the icon to display.
            tooltip (str): The tooltip text to show on hover.
            connection (callable): The function or method to connect to the button's clicked signal.
        """
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
        """Retrieves a button widget by its ID.

        Args:
            btn_id (str): The identifier of the button to retrieve.

        Returns:
            QPushButton | None: The button widget if found, otherwise None.
        """
        return self.buttons.get(btn_id)

    def add_custom_button(self, btn_id, text, icon, tooltip, connection):
        """Adds a new custom button to the panel at runtime.

        Args:
            btn_id (str): A unique identifier for the button.
            text (str): The text to display on the button.
            icon (str): The filename of the icon to display.
            tooltip (str): The tooltip text to show on hover.
            connection (callable): The function to connect to the button's clicked signal.
        """
        self.add_button(btn_id, text, icon, tooltip, connection)

    def remove_button(self, btn_id):
        """Removes a button from the panel by its ID.

        Args:
            btn_id (str): The identifier of the button to remove.
        """
        if btn_id in self.buttons:
            button = self.buttons.pop(btn_id)
            self.layout.removeWidget(button)
            button.deleteLater()

    def enable_button(self, btn_id, enabled=True):
        """Enables or disables a button by its ID.

        Args:
            btn_id (str): The identifier of the button to modify.
            enabled (bool, optional): True to enable the button, False to disable it.
                                      Defaults to True.
        """
        if btn_id in self.buttons:
            self.buttons[btn_id].setEnabled(enabled)
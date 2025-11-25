from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, pyqtSignal
from helper import resource_path

class ControlPanel(QWidget):
    """A widget that contains the main control buttons for the application.

    This panel groups buttons for core actions like adding files, running
    the conversion process, stopping it, removing files, and managing presets.
    It provides a centralized location for user interaction with the main
    functionalities of the application.
    """
    # Define signals for each button action
    add_files_clicked = pyqtSignal()
    run_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    remove_clicked = pyqtSignal()
    cut_video_clicked = pyqtSignal()
    join_video_clicked = pyqtSignal()
    crop_video_clicked = pyqtSignal()
    set_thumbnail_clicked = pyqtSignal()
    add_preset_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initializes the ControlPanel widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()

    def _setup_ui(self):
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
        self._setup_buttons()

    def _setup_buttons(self):
        """Initializes and configures all the standard control buttons.

        This method defines a dictionary of button configurations and uses it
        to create and add each button to the panel.
        """
        button_configs = {
            'add_files': {
                'text': ' Add files',
                'icon': 'add-files.png',
                'tooltip': 'Add files to the list',
                'connection': self.add_files_clicked.emit
            },
            'run': {
                'text': ' Run',
                'icon': 'run.png',
                'tooltip': 'Start processing files',
                'connection': self.run_clicked.emit
            },
            'stop': {
                'text': ' Stop',
                'icon': 'stop.png',
                'tooltip': 'Stop processing',
                'connection': self.stop_clicked.emit
            },
            'remove': {
                'text': ' Remove',
                'icon': 'remove.png',
                'tooltip': 'Remove selected files',
                'connection': self.remove_clicked.emit
            },
            'cut_video': {
                'text': ' Cut Video',
                'icon': 'cut-video.png',
                'tooltip': 'Cut a video into segments',
                'connection': self.cut_video_clicked.emit
            },
            'join_video': {
                'text': ' Join Video',
                'icon': 'join-video.png',
                'tooltip': 'Join multiple videos into one',
                'connection': self.join_video_clicked.emit
            },
            'crop_video': {
                'text': ' Crop Video',
                'icon': 'crop-video.png',
                'tooltip': 'Crop a video',
                'connection': self.crop_video_clicked.emit
            },
            'set_thumbnail': {
                'text': ' Set Thumbnail',
                'icon': 'set-thumbnail.png',
                'tooltip': 'Set a thumbnail for a video',
                'connection': self.set_thumbnail_clicked.emit
            },
            'add_preset': {
                'text': ' Add preset',
                'icon': 'add-preset.png',
                'tooltip': 'Add new preset',
                'connection': self.add_preset_clicked.emit
            }
        }

        for btn_id, config in button_configs.items():
            self._add_button(btn_id, **config)

    def _add_button(self, btn_id, text, icon, tooltip, connection):
        """Creates and adds a single button to the control panel.

        This is a factory method used by `_setup_buttons` and `add_custom_button`.

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
        self._add_button(btn_id, text, icon, tooltip, connection)

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
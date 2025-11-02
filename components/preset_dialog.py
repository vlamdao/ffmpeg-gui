
from PyQt5.QtWidgets import (
    QGroupBox, QDialog, QTextEdit,
    QLineEdit, QDialogButtonBox, QVBoxLayout,
    QHBoxLayout
)
from PyQt5.QtGui import QFont, QIcon
from helper import resource_path
from .placeholders import PlaceholdersTable, Placeholders


class PresetDialog(QDialog):
    """A dialog for adding or editing a preset (name and command)."""
    _INPUT_WIDTH = 700
    _CMD_INPUT_HEIGHT = 50

    def __init__(self, parent=None, title="Preset", preset_name="", preset_command=""):
        """Initializes the PresetDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            title (str, optional): The window title for the dialog. Defaults to "Preset".
            preset_name (str, optional): The initial text for the preset name field. Defaults to "".
            preset_command (str, optional): The initial text for the command field. Defaults to "".
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(resource_path("icon/add-preset.png")))
        self.setMinimumWidth(self._INPUT_WIDTH)
        self._preset_name = preset_name
        self._preset_command = preset_command
        self._setup_ui()

    def _setup_ui(self):
        """Initializes and arranges all UI components."""
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Creates all the widgets needed for the dialog."""
        self._name_input = QLineEdit(self._preset_name)

        GENERAL_PLACEHOLDERS = Placeholders().get_placeholders_list()
        self._placeholders_table = PlaceholdersTable(
            placeholders_list=GENERAL_PLACEHOLDERS,
            num_columns=4,
            parent=self
        )
        self._placeholders_table.set_compact_height()

        self._cmd_input = QTextEdit(self._preset_command)
        self._cmd_input.setFont(QFont("Consolas", 9))
        self._cmd_input.setMinimumHeight(self._CMD_INPUT_HEIGHT)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        self._placeholders_table.placeholder_double_clicked.connect(self._cmd_input.insertPlainText)
        
    def _setup_layout(self):
        """Configures the layout and adds widgets to it."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        name_group = QGroupBox("Preset Name")
        name_layout = QHBoxLayout()
        name_layout.addWidget(self._name_input)
        name_group.setLayout(name_layout)

        placeholder_group = QGroupBox("Placeholders")
        placeholder_layout = QHBoxLayout()
        placeholder_layout.addWidget(self._placeholders_table)
        placeholder_group.setLayout(placeholder_layout)

        cmd_group = QGroupBox("Command")
        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(self._cmd_input)
        cmd_group.setLayout(cmd_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._button_box)

        self.main_layout.addWidget(name_group)
        self.main_layout.addWidget(placeholder_group)
        self.main_layout.addWidget(cmd_group)
        self.main_layout.addLayout(button_layout)

    def get_preset(self):
        """Returns the preset name and command from the input fields."""
        return self._name_input.text().strip(), self._cmd_input.toPlainText().strip()
